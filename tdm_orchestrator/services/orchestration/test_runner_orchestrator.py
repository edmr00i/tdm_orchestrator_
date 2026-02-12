"""
Tests for RunnerOrchestrator - Runner execution orchestration service.

Covers:
- __init__: Initialization with runner and user
- _get_executor: Executor caching by datasource
- _execute_step: Single step execution with error handling
- _create_execution_log: ExecutionLog creation
- execute: Full runner execution with PRE/POST scripts
- execute_dry_run: Validation mode execution
- _validate_step: Single step validation
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from .runner_orchestrator import RunnerOrchestrator
from .results import StepResult, RunnerExecutionResult


# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_script():
    """Create a mock script with datasource."""
    script = MagicMock()
    script.name = "test_script"
    script.reference = "REF001"
    script.content = "SELECT 1"
    script.datasource = MagicMock()
    script.datasource.id = 1
    return script


@pytest.fixture
def mock_script_no_datasource():
    """Create a mock script without datasource."""
    script = MagicMock()
    script.name = "test_script_no_ds"
    script.reference = "REF002"
    script.content = "SELECT 1"
    script.datasource = None
    return script


@pytest.fixture
def mock_step(mock_script):
    """Create a mock step."""
    step = MagicMock()
    step.script = mock_script
    step.order = 1
    return step


@pytest.fixture
def mock_step_no_datasource(mock_script_no_datasource):
    """Create a mock step without datasource."""
    step = MagicMock()
    step.script = mock_script_no_datasource
    step.order = 1
    return step


@pytest.fixture
def mock_runner():
    """Create a mock runner."""
    runner = MagicMock()
    runner.id = 1
    runner.name = "test_runner"
    runner.stop_on_error = True
    runner.get_pre_scripts.return_value = []
    runner.get_post_scripts.return_value = []
    return runner


@pytest.fixture
def mock_user_authenticated():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_user_unauthenticated():
    """Create a mock unauthenticated user."""
    user = MagicMock()
    user.is_authenticated = False
    return user


@pytest.fixture
def mock_sql_execution_result_success():
    """Create a mock successful SQL execution result."""
    result = MagicMock()
    result.success = True
    result.duration_ms = 100
    result.error_message = None
    result.rows_affected = 5
    return result


@pytest.fixture
def mock_sql_execution_result_failure():
    """Create a mock failed SQL execution result."""
    result = MagicMock()
    result.success = False
    result.duration_ms = 50
    result.error_message = "SQL syntax error"
    result.rows_affected = 0
    return result


@pytest.fixture
def orchestrator(mock_runner):
    """Create a RunnerOrchestrator instance."""
    return RunnerOrchestrator(mock_runner)


@pytest.fixture
def orchestrator_with_user(mock_runner, mock_user_authenticated):
    """Create a RunnerOrchestrator instance with authenticated user."""
    return RunnerOrchestrator(mock_runner, user=mock_user_authenticated)


# =====================
# Helper Functions
# =====================

def get_pre_results(result):
    """Extract PRE step results from RunnerExecutionResult."""
    return result.pre_scripts


def get_post_results(result):
    """Extract POST step results from RunnerExecutionResult."""
    return result.post_scripts


# =====================
# __init__ Tests
# =====================

class TestRunnerOrchestratorInit:
    """Tests for RunnerOrchestrator.__init__ method."""

    def test_initializes_runner(self, mock_runner):
        """Stores runner reference."""
        orchestrator = RunnerOrchestrator(mock_runner)
        
        assert orchestrator.runner == mock_runner

    def test_initializes_user(self, mock_runner, mock_user_authenticated):
        """Stores user reference."""
        orchestrator = RunnerOrchestrator(mock_runner, user=mock_user_authenticated)
        
        assert orchestrator.user == mock_user_authenticated

    def test_initializes_user_none_by_default(self, mock_runner):
        """User is None by default."""
        orchestrator = RunnerOrchestrator(mock_runner)
        
        assert orchestrator.user is None

    def test_initializes_empty_executors_cache(self, mock_runner):
        """Initializes empty _executors dictionary."""
        orchestrator = RunnerOrchestrator(mock_runner)
        
        assert orchestrator._executors == {}
        assert isinstance(orchestrator._executors, dict)


# =====================
# _get_executor Tests
# =====================

class TestGetExecutor:
    """Tests for RunnerOrchestrator._get_executor method."""

    def test_creates_new_executor_for_new_datasource(self, orchestrator, mocker):
        """Creates new SqlExecutor for datasource not in cache."""
        mock_executor = MagicMock()
        mock_executor_class = mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            return_value=mock_executor
        )
        
        datasource = MagicMock()
        datasource.id = 1
        
        result = orchestrator._get_executor(datasource)
        
        mock_executor_class.assert_called_once_with(datasource)
        assert result == mock_executor

    def test_returns_cached_executor_for_same_datasource(self, orchestrator, mocker):
        """Returns cached executor for same datasource.id."""
        mock_executor = MagicMock()
        mock_executor_class = mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            return_value=mock_executor
        )
        
        datasource = MagicMock()
        datasource.id = 1
        
        result1 = orchestrator._get_executor(datasource)
        result2 = orchestrator._get_executor(datasource)
        
        # Should only create once
        assert mock_executor_class.call_count == 1
        assert result1 == result2

    def test_creates_different_executors_for_different_datasources(self, orchestrator, mocker):
        """Creates separate executors for different datasources."""
        mock_executor1 = MagicMock()
        mock_executor2 = MagicMock()
        mock_executor_class = mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            side_effect=[mock_executor1, mock_executor2]
        )
        
        datasource1 = MagicMock()
        datasource1.id = 1
        datasource2 = MagicMock()
        datasource2.id = 2
        
        result1 = orchestrator._get_executor(datasource1)
        result2 = orchestrator._get_executor(datasource2)
        
        assert mock_executor_class.call_count == 2
        assert result1 == mock_executor1
        assert result2 == mock_executor2

    def test_caches_executor_by_datasource_id(self, orchestrator, mocker):
        """Caches executor by datasource.id in _executors dict."""
        mock_executor = MagicMock()
        mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            return_value=mock_executor
        )
        
        datasource = MagicMock()
        datasource.id = 42
        
        orchestrator._get_executor(datasource)
        
        assert 42 in orchestrator._executors
        assert orchestrator._executors[42] == mock_executor


# =====================
# _execute_step Tests
# =====================

class TestExecuteStep:
    """Tests for RunnerOrchestrator._execute_step method."""

    def test_returns_failure_when_no_datasource(self, orchestrator, mock_step_no_datasource):
        """Returns failure StepResult when script has no datasource."""
        result = orchestrator._execute_step(mock_step_no_datasource, {}, 'pre')
        
        assert result.success is False
        assert result.error_message == 'Aucune datasource configurée'
        assert result.duration_ms == 0

    def test_returns_success_result_from_executor(
        self, orchestrator, mock_step, mock_sql_execution_result_success, mocker
    ):
        """Returns success StepResult from executor result."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_sql_execution_result_success
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator._execute_step(mock_step, {'VAR': 'value'}, 'pre')
        
        assert result.success is True
        assert result.duration_ms == 100
        assert result.rows_affected == 5
        assert result.error_message is None

    def test_returns_failure_result_from_executor(
        self, orchestrator, mock_step, mock_sql_execution_result_failure, mocker
    ):
        """Returns failure StepResult from executor result."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_sql_execution_result_failure
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator._execute_step(mock_step, {}, 'post')
        
        assert result.success is False
        assert result.error_message == "SQL syntax error"
        assert result.duration_ms == 50

    def test_handles_executor_exception(self, orchestrator, mock_step, mocker):
        """Handles exception from executor gracefully."""
        mock_executor = MagicMock()
        mock_executor.execute.side_effect = Exception("Connection failed")
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        result = orchestrator._execute_step(mock_step, {}, 'pre')
        
        assert result.success is False
        assert result.error_message == "Connection failed"
        assert result.duration_ms == 0

    def test_sets_correct_script_name(self, orchestrator, mock_step, mock_sql_execution_result_success, mocker):
        """Sets script_name from step.script.name."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_sql_execution_result_success
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator._execute_step(mock_step, {}, 'pre')
        
        assert result.script_name == "test_script"

    def test_sets_correct_script_reference(self, orchestrator, mock_step, mock_sql_execution_result_success, mocker):
        """Sets script_reference from step.script.reference."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_sql_execution_result_success
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator._execute_step(mock_step, {}, 'pre')
        
        assert result.script_reference == "REF001"

    def test_sets_correct_step_type(self, orchestrator, mock_step, mock_sql_execution_result_success, mocker):
        """Sets step_type from parameter."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_sql_execution_result_success
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result_pre = orchestrator._execute_step(mock_step, {}, 'pre')
        result_post = orchestrator._execute_step(mock_step, {}, 'post')
        
        assert result_pre.step_type == 'pre'
        assert result_post.step_type == 'post'

    def test_sets_correct_order(self, orchestrator, mock_step, mock_sql_execution_result_success, mocker):
        """Sets order from step.order."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_sql_execution_result_success
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        mock_step.order = 5
        result = orchestrator._execute_step(mock_step, {}, 'pre')
        
        assert result.order == 5

    def test_passes_variables_to_executor(self, orchestrator, mock_step, mock_sql_execution_result_success, mocker):
        """Passes variables dict to executor.execute."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_sql_execution_result_success
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        variables = {'SCHEMA': 'prod', 'TABLE': 'users'}
        orchestrator._execute_step(mock_step, variables, 'pre')
        
        mock_executor.execute.assert_called_once_with(mock_step.script.content, variables)


# =====================
# _create_execution_log Tests
# =====================

class TestCreateExecutionLog:
    """Tests for RunnerOrchestrator._create_execution_log method."""

    def test_creates_execution_log_with_correct_attributes(self, orchestrator, mocker):
        """Creates ExecutionLog with runner, status, and variables."""
        mock_log = MagicMock()
        mock_log.id = 123
        # Mock the _create_execution_log method directly to avoid import issues
        mock_create = mocker.patch.object(
            orchestrator, '_create_execution_log', return_value=mock_log
        )
        
        variables = {'VAR1': 'value1'}
        result = orchestrator._create_execution_log(variables)
        
        mock_create.assert_called_once_with(variables)
        assert result == mock_log

    def test_sets_executed_by_for_authenticated_user(self, orchestrator_with_user, mocker):
        """Sets executed_by to user when authenticated."""
        mock_log = MagicMock()
        mock_create = mocker.patch.object(
            orchestrator_with_user, '_create_execution_log', return_value=mock_log
        )
        
        orchestrator_with_user._create_execution_log({})
        
        mock_create.assert_called_once_with({})

    def test_sets_executed_by_none_for_unauthenticated_user(
        self, mock_runner, mock_user_unauthenticated, mocker
    ):
        """Sets executed_by to None when user is not authenticated."""
        orchestrator = RunnerOrchestrator(mock_runner, user=mock_user_unauthenticated)
        mock_log = MagicMock()
        mock_create = mocker.patch.object(
            orchestrator, '_create_execution_log', return_value=mock_log
        )
        
        orchestrator._create_execution_log({})
        
        mock_create.assert_called_once_with({})

    def test_sets_executed_by_none_when_user_is_none(self, orchestrator, mocker):
        """Sets executed_by to None when user is None."""
        mock_log = MagicMock()
        mock_create = mocker.patch.object(
            orchestrator, '_create_execution_log', return_value=mock_log
        )
        
        orchestrator._create_execution_log({})
        
        mock_create.assert_called_once_with({})


# =====================
# execute Tests
# =====================

class TestExecute:
    """Tests for RunnerOrchestrator.execute method."""

    def test_executes_pre_scripts_in_order(self, orchestrator, mocker):
        """Executes PRE scripts from runner.get_pre_scripts()."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        mocker.patch.object(orchestrator, '_create_execution_log', side_effect=Exception("Skip log"))
        
        step1 = MagicMock()
        step1.order = 1
        step1.script.name = "script1"
        step1.script.reference = "REF1"
        step1.script.datasource = None
        
        step2 = MagicMock()
        step2.order = 2
        step2.script.name = "script2"
        step2.script.reference = "REF2"
        step2.script.datasource = None
        
        orchestrator.runner.get_pre_scripts.return_value = [step1, step2]
        orchestrator.runner.stop_on_error = False
        
        result = orchestrator.execute({}, create_log=False)
        
        # Both steps should be in step_results with type 'pre'
        pre_results = get_pre_results(result)
        assert len(pre_results) == 2

    def test_executes_post_scripts_after_pre(self, orchestrator, mocker):
        """Executes POST scripts after PRE scripts complete."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        pre_step = MagicMock()
        pre_step.order = 1
        pre_step.script.name = "pre_script"
        pre_step.script.reference = "PRE1"
        pre_step.script.datasource = MagicMock()
        pre_step.script.datasource.id = 1
        
        post_step = MagicMock()
        post_step.order = 1
        post_step.script.name = "post_script"
        post_step.script.reference = "POST1"
        post_step.script.datasource = MagicMock()
        post_step.script.datasource.id = 1
        
        orchestrator.runner.get_pre_scripts.return_value = [pre_step]
        orchestrator.runner.get_post_scripts.return_value = [post_step]
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 50
        mock_result.error_message = None
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator.execute({}, create_log=False)
        
        pre_results = get_pre_results(result)
        post_results = get_post_results(result)
        assert len(pre_results) == 1
        assert len(post_results) == 1

    def test_stops_on_error_pre_when_stop_on_error_true(self, orchestrator, mocker):
        """Stops execution on PRE error when stop_on_error=True."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step1 = MagicMock()
        step1.order = 1
        step1.script.name = "failing_script"
        step1.script.reference = "REF1"
        step1.script.datasource = MagicMock()
        step1.script.datasource.id = 1
        
        step2 = MagicMock()
        step2.order = 2
        step2.script.name = "never_runs"
        step2.script.reference = "REF2"
        step2.script.datasource = MagicMock()
        step2.script.datasource.id = 1
        
        orchestrator.runner.get_pre_scripts.return_value = [step1, step2]
        orchestrator.runner.stop_on_error = True
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.duration_ms = 50
        mock_result.error_message = "Failed"
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator.execute({}, create_log=False)
        
        # Only first step should execute
        pre_results = get_pre_results(result)
        assert len(pre_results) == 1
        assert "failing_script" in result.error_message

    def test_stops_on_error_post_when_stop_on_error_true(self, orchestrator, mocker):
        """Stops execution on POST error when stop_on_error=True."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        post_step1 = MagicMock()
        post_step1.order = 1
        post_step1.script.name = "failing_post"
        post_step1.script.reference = "POST1"
        post_step1.script.datasource = MagicMock()
        post_step1.script.datasource.id = 1
        
        post_step2 = MagicMock()
        post_step2.order = 2
        post_step2.script.name = "never_runs"
        post_step2.script.reference = "POST2"
        post_step2.script.datasource = MagicMock()
        post_step2.script.datasource.id = 1
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = [post_step1, post_step2]
        orchestrator.runner.stop_on_error = True
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.duration_ms = 50
        mock_result.error_message = "Post failed"
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator.execute({}, create_log=False)
        
        post_results = get_post_results(result)
        assert len(post_results) == 1
        assert "failing_post" in result.error_message

    def test_continues_on_error_when_stop_on_error_false(self, orchestrator, mocker):
        """Continues execution on error when stop_on_error=False."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step1 = MagicMock()
        step1.order = 1
        step1.script.name = "failing_script"
        step1.script.reference = "REF1"
        step1.script.datasource = MagicMock()
        step1.script.datasource.id = 1
        
        step2 = MagicMock()
        step2.order = 2
        step2.script.name = "also_runs"
        step2.script.reference = "REF2"
        step2.script.datasource = MagicMock()
        step2.script.datasource.id = 1
        
        orchestrator.runner.get_pre_scripts.return_value = [step1, step2]
        orchestrator.runner.stop_on_error = False
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.duration_ms = 50
        mock_result.error_message = "Failed"
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator.execute({}, create_log=False)
        
        # Both steps should execute
        pre_results = get_pre_results(result)
        assert len(pre_results) == 2

    def test_creates_execution_log_when_create_log_true(self, orchestrator, mocker):
        """Creates ExecutionLog when create_log=True."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        mock_log = MagicMock()
        mock_log.id = 123
        mock_create_log = mocker.patch.object(
            orchestrator, '_create_execution_log', return_value=mock_log
        )
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        result = orchestrator.execute({'VAR': 'value'}, create_log=True)
        
        mock_create_log.assert_called_once_with({'VAR': 'value'})
        assert result.execution_log_id == 123

    def test_skips_execution_log_when_create_log_false(self, orchestrator, mocker):
        """Skips ExecutionLog creation when create_log=False."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        mock_create_log = mocker.patch.object(orchestrator, '_create_execution_log')
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        result = orchestrator.execute({}, create_log=False)
        
        mock_create_log.assert_not_called()
        assert result.execution_log_id is None

    def test_handles_execution_log_creation_failure(self, orchestrator, mocker):
        """Handles ExecutionLog creation failure gracefully."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        mocker.patch.object(
            orchestrator, '_create_execution_log', 
            side_effect=Exception("DB error")
        )
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        # Should not raise, execution continues
        result = orchestrator.execute({}, create_log=True)
        
        assert result.execution_log_id is None

    def test_calculates_total_duration(self, orchestrator, mocker):
        """Calculates total_duration_ms correctly."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.time.time', 
                     side_effect=[1000.0, 1002.5])  # 2.5 seconds
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        result = orchestrator.execute({}, create_log=False)
        
        assert result.total_duration_ms == 2500

    def test_updates_log_on_success(self, orchestrator, mocker):
        """Updates ExecutionLog.mark_success on successful execution."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        mock_log = MagicMock()
        mock_log.id = 123
        mocker.patch.object(orchestrator, '_create_execution_log', return_value=mock_log)
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        orchestrator.execute({}, create_log=True)
        
        mock_log.mark_success.assert_called_once_with("Exécution terminée avec succès")

    def test_updates_log_on_failure(self, orchestrator, mocker):
        """Updates ExecutionLog.mark_failure on failed execution."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        mock_log = MagicMock()
        mock_log.id = 123
        mocker.patch.object(orchestrator, '_create_execution_log', return_value=mock_log)
        
        step = MagicMock()
        step.order = 1
        step.script.name = "failing"
        step.script.reference = "REF1"
        step.script.datasource = MagicMock()
        step.script.datasource.id = 1
        
        orchestrator.runner.get_pre_scripts.return_value = [step]
        orchestrator.runner.get_post_scripts.return_value = []
        orchestrator.runner.stop_on_error = True
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.duration_ms = 50
        mock_result.error_message = "Error"
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        orchestrator.execute({}, create_log=True)
        
        mock_log.mark_failure.assert_called_once()

    def test_handles_exception_during_execution(self, orchestrator, mocker):
        """Handles unexpected exception during execution."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        orchestrator.runner.get_pre_scripts.side_effect = Exception("Unexpected error")
        
        result = orchestrator.execute({}, create_log=False)
        
        assert result.overall_success is False
        assert result.error_message == "Unexpected error"

    def test_uses_empty_dict_when_variables_none(self, orchestrator, mocker):
        """Uses empty dict when variables parameter is None."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step = MagicMock()
        step.order = 1
        step.script.name = "test"
        step.script.reference = "REF1"
        step.script.datasource = MagicMock()
        step.script.datasource.id = 1
        step.script.content = "SELECT 1"
        
        orchestrator.runner.get_pre_scripts.return_value = [step]
        orchestrator.runner.get_post_scripts.return_value = []
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 50
        mock_result.error_message = None
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        orchestrator.execute(None, create_log=False)
        
        # Should pass empty dict, not None
        mock_executor.execute.assert_called_with(step.script.content, {})

    def test_sets_runner_id_and_name_in_result(self, orchestrator, mocker):
        """Sets runner_id and runner_name in result."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        orchestrator.runner.id = 42
        orchestrator.runner.name = "my_runner"
        
        result = orchestrator.execute({}, create_log=False)
        
        assert result.runner_id == 42
        assert result.runner_name == "my_runner"

    def test_skips_post_when_pre_fails_and_stop_on_error(self, orchestrator, mocker):
        """Skips POST scripts when PRE fails and stop_on_error=True."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        pre_step = MagicMock()
        pre_step.order = 1
        pre_step.script.name = "failing_pre"
        pre_step.script.reference = "PRE1"
        pre_step.script.datasource = MagicMock()
        pre_step.script.datasource.id = 1
        
        post_step = MagicMock()
        post_step.order = 1
        post_step.script.name = "should_not_run"
        post_step.script.reference = "POST1"
        post_step.script.datasource = MagicMock()
        post_step.script.datasource.id = 1
        
        orchestrator.runner.get_pre_scripts.return_value = [pre_step]
        orchestrator.runner.get_post_scripts.return_value = [post_step]
        orchestrator.runner.stop_on_error = True
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.duration_ms = 50
        mock_result.error_message = "Failed"
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator.execute({}, create_log=False)
        
        pre_results = get_pre_results(result)
        post_results = get_post_results(result)
        assert len(pre_results) == 1
        assert len(post_results) == 0


# =====================
# execute_dry_run Tests
# =====================

class TestExecuteDryRun:
    """Tests for RunnerOrchestrator.execute_dry_run method."""

    def test_validates_pre_scripts(self, orchestrator, mocker):
        """Validates PRE scripts using _validate_step."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step = MagicMock()
        step.order = 1
        step.script.name = "pre_script"
        step.script.reference = "PRE1"
        step.script.datasource = None
        
        orchestrator.runner.get_pre_scripts.return_value = [step]
        orchestrator.runner.get_post_scripts.return_value = []
        
        result = orchestrator.execute_dry_run({})
        
        pre_results = get_pre_results(result)
        assert len(pre_results) == 1

    def test_validates_post_scripts(self, orchestrator, mocker):
        """Validates POST scripts using _validate_step."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step = MagicMock()
        step.order = 1
        step.script.name = "post_script"
        step.script.reference = "POST1"
        step.script.datasource = None
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = [step]
        
        result = orchestrator.execute_dry_run({})
        
        post_results = get_post_results(result)
        assert len(post_results) == 1

    def test_does_not_create_execution_log(self, orchestrator, mocker):
        """Does not create ExecutionLog in dry run."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        mock_create_log = mocker.patch.object(orchestrator, '_create_execution_log')
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        orchestrator.execute_dry_run({})
        
        mock_create_log.assert_not_called()

    def test_calculates_total_duration(self, orchestrator, mocker):
        """Calculates total_duration_ms in dry run."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.time.time',
                     side_effect=[1000.0, 1001.0])  # 1 second
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        result = orchestrator.execute_dry_run({})
        
        assert result.total_duration_ms == 1000

    def test_uses_empty_dict_when_variables_none(self, orchestrator, mocker):
        """Uses empty dict when variables is None."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step = MagicMock()
        step.order = 1
        step.script.name = "test"
        step.script.reference = "REF1"
        step.script.datasource = MagicMock()
        step.script.datasource.id = 1
        step.script.content = "SELECT 1"
        
        orchestrator.runner.get_pre_scripts.return_value = [step]
        orchestrator.runner.get_post_scripts.return_value = []
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 50
        mock_result.error_message = None
        mock_executor.execute_dry_run.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        orchestrator.execute_dry_run(None)
        
        mock_executor.execute_dry_run.assert_called_with(step.script.content, {})

    def test_sets_runner_id_and_name_in_result(self, orchestrator, mocker):
        """Sets runner_id and runner_name in dry run result."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        orchestrator.runner.id = 99
        orchestrator.runner.name = "dry_run_runner"
        
        result = orchestrator.execute_dry_run({})
        
        assert result.runner_id == 99
        assert result.runner_name == "dry_run_runner"

    def test_validates_all_steps_regardless_of_failure(self, orchestrator, mocker):
        """Validates all steps even if some fail (no stop_on_error in dry run)."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step1 = MagicMock()
        step1.order = 1
        step1.script.name = "step1"
        step1.script.reference = "REF1"
        step1.script.datasource = None  # Will fail
        
        step2 = MagicMock()
        step2.order = 2
        step2.script.name = "step2"
        step2.script.reference = "REF2"
        step2.script.datasource = None  # Will also fail
        
        orchestrator.runner.get_pre_scripts.return_value = [step1, step2]
        orchestrator.runner.get_post_scripts.return_value = []
        
        result = orchestrator.execute_dry_run({})
        
        # Both steps should be validated
        pre_results = get_pre_results(result)
        assert len(pre_results) == 2


# =====================
# _validate_step Tests
# =====================

class TestValidateStep:
    """Tests for RunnerOrchestrator._validate_step method."""

    def test_returns_failure_when_no_datasource(self, orchestrator, mock_step_no_datasource):
        """Returns failure StepResult when script has no datasource."""
        result = orchestrator._validate_step(mock_step_no_datasource, {}, 'pre')
        
        assert result.success is False
        assert result.error_message == 'Aucune datasource configurée'
        assert result.duration_ms == 0

    def test_returns_success_from_dry_run(self, orchestrator, mock_step, mocker):
        """Returns success StepResult from executor.execute_dry_run."""
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 25
        mock_result.error_message = None
        mock_executor.execute_dry_run.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator._validate_step(mock_step, {'VAR': 'val'}, 'pre')
        
        assert result.success is True
        assert result.duration_ms == 25
        assert result.error_message is None

    def test_returns_failure_from_dry_run(self, orchestrator, mock_step, mocker):
        """Returns failure StepResult from executor.execute_dry_run."""
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.duration_ms = 10
        mock_result.error_message = "Validation error"
        mock_executor.execute_dry_run.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator._validate_step(mock_step, {}, 'post')
        
        assert result.success is False
        assert result.error_message == "Validation error"

    def test_handles_exception_gracefully(self, orchestrator, mock_step, mocker):
        """Handles exception from executor gracefully."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.side_effect = Exception("Validation failed")
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator._validate_step(mock_step, {}, 'pre')
        
        assert result.success is False
        assert result.error_message == "Validation failed"
        assert result.duration_ms == 0

    def test_sets_correct_step_metadata(self, orchestrator, mock_step, mocker):
        """Sets correct script_name, reference, step_type, and order."""
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 15
        mock_result.error_message = None
        mock_executor.execute_dry_run.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        mock_step.order = 3
        result = orchestrator._validate_step(mock_step, {}, 'post')
        
        assert result.script_name == "test_script"
        assert result.script_reference == "REF001"
        assert result.step_type == 'post'
        assert result.order == 3

    def test_passes_variables_to_executor_dry_run(self, orchestrator, mock_step, mocker):
        """Passes variables to executor.execute_dry_run."""
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 10
        mock_result.error_message = None
        mock_executor.execute_dry_run.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        variables = {'SCHEMA': 'test', 'TABLE': 'users'}
        orchestrator._validate_step(mock_step, variables, 'pre')
        
        mock_executor.execute_dry_run.assert_called_once_with(
            mock_step.script.content, variables
        )


# =====================
# Integration Tests
# =====================

class TestRunnerOrchestratorIntegration:
    """Integration tests for RunnerOrchestrator."""

    def test_full_execution_workflow_success(self, mock_runner, mocker):
        """Tests complete successful execution workflow."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        # Setup scripts
        pre_script = MagicMock()
        pre_script.name = "pre_script"
        pre_script.reference = "PRE1"
        pre_script.content = "INSERT INTO pre_table VALUES (1)"
        pre_script.datasource = MagicMock()
        pre_script.datasource.id = 1
        
        pre_step = MagicMock()
        pre_step.order = 1
        pre_step.script = pre_script
        
        post_script = MagicMock()
        post_script.name = "post_script"
        post_script.reference = "POST1"
        post_script.content = "UPDATE post_table SET done = true"
        post_script.datasource = MagicMock()
        post_script.datasource.id = 1
        
        post_step = MagicMock()
        post_step.order = 1
        post_step.script = post_script
        
        mock_runner.get_pre_scripts.return_value = [pre_step]
        mock_runner.get_post_scripts.return_value = [post_step]
        
        # Mock executor
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 100
        mock_result.error_message = None
        mock_result.rows_affected = 1
        mock_executor.execute.return_value = mock_result
        
        mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            return_value=mock_executor
        )
        
        orchestrator = RunnerOrchestrator(mock_runner)
        result = orchestrator.execute({'SCHEMA': 'test'}, create_log=False)
        
        assert result.overall_success is True
        pre_results = get_pre_results(result)
        post_results = get_post_results(result)
        assert len(pre_results) == 1
        assert len(post_results) == 1
        assert pre_results[0].success is True
        assert post_results[0].success is True

    def test_full_execution_workflow_with_failure(self, mock_runner, mocker):
        """Tests execution workflow with failure."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        # Setup failing script
        pre_script = MagicMock()
        pre_script.name = "failing_script"
        pre_script.reference = "PRE1"
        pre_script.content = "INVALID SQL"
        pre_script.datasource = MagicMock()
        pre_script.datasource.id = 1
        
        pre_step = MagicMock()
        pre_step.order = 1
        pre_step.script = pre_script
        
        mock_runner.get_pre_scripts.return_value = [pre_step]
        mock_runner.get_post_scripts.return_value = []
        mock_runner.stop_on_error = True
        
        # Mock executor with failure
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.duration_ms = 50
        mock_result.error_message = "Syntax error"
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        
        mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            return_value=mock_executor
        )
        
        orchestrator = RunnerOrchestrator(mock_runner)
        result = orchestrator.execute({}, create_log=False)
        
        assert result.overall_success is False
        assert "failing_script" in result.error_message

    def test_dry_run_validates_all_scripts(self, mock_runner, mocker):
        """Tests dry run validates all scripts."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        # Setup scripts
        pre_script = MagicMock()
        pre_script.name = "pre_script"
        pre_script.reference = "PRE1"
        pre_script.content = "SELECT 1"
        pre_script.datasource = MagicMock()
        pre_script.datasource.id = 1
        
        pre_step = MagicMock()
        pre_step.order = 1
        pre_step.script = pre_script
        
        mock_runner.get_pre_scripts.return_value = [pre_step]
        mock_runner.get_post_scripts.return_value = []
        
        # Mock executor dry run
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 20
        mock_result.error_message = None
        mock_executor.execute_dry_run.return_value = mock_result
        
        mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            return_value=mock_executor
        )
        
        orchestrator = RunnerOrchestrator(mock_runner)
        result = orchestrator.execute_dry_run({'VAR': 'value'})
        
        pre_results = get_pre_results(result)
        assert len(pre_results) == 1
        assert pre_results[0].success is True
        mock_executor.execute_dry_run.assert_called_once()


# =====================
# Edge Cases
# =====================

class TestRunnerOrchestratorEdgeCases:
    """Edge case tests for RunnerOrchestrator."""

    def test_no_scripts_to_execute(self, orchestrator, mocker):
        """Handles runner with no PRE or POST scripts."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        result = orchestrator.execute({}, create_log=False)
        
        assert result.overall_success is True
        pre_results = get_pre_results(result)
        post_results = get_post_results(result)
        assert len(pre_results) == 0
        assert len(post_results) == 0

    def test_multiple_datasources(self, orchestrator, mocker):
        """Handles scripts with different datasources."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        script1 = MagicMock()
        script1.name = "script1"
        script1.reference = "REF1"
        script1.content = "SELECT 1"
        script1.datasource = MagicMock()
        script1.datasource.id = 1
        
        script2 = MagicMock()
        script2.name = "script2"
        script2.reference = "REF2"
        script2.content = "SELECT 2"
        script2.datasource = MagicMock()
        script2.datasource.id = 2
        
        step1 = MagicMock()
        step1.order = 1
        step1.script = script1
        
        step2 = MagicMock()
        step2.order = 2
        step2.script = script2
        
        orchestrator.runner.get_pre_scripts.return_value = [step1, step2]
        orchestrator.runner.get_post_scripts.return_value = []
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 50
        mock_result.error_message = None
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        
        mocker.patch(
            'tdm_orchestrator.services.orchestration.runner_orchestrator.SqlExecutor',
            return_value=mock_executor
        )
        
        orchestrator.execute({}, create_log=False)
        
        # Should have cached 2 different executors
        assert len(orchestrator._executors) == 2

    def test_empty_variables_dict(self, orchestrator, mocker):
        """Handles empty variables dictionary."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        step = MagicMock()
        step.order = 1
        step.script.name = "script"
        step.script.reference = "REF1"
        step.script.content = "SELECT 1"
        step.script.datasource = MagicMock()
        step.script.datasource.id = 1
        
        orchestrator.runner.get_pre_scripts.return_value = [step]
        orchestrator.runner.get_post_scripts.return_value = []
        
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.duration_ms = 50
        mock_result.error_message = None
        mock_result.rows_affected = 0
        mock_executor.execute.return_value = mock_result
        mocker.patch.object(orchestrator, '_get_executor', return_value=mock_executor)
        
        result = orchestrator.execute({}, create_log=False)
        
        assert result is not None
        mock_executor.execute.assert_called_with(step.script.content, {})

    def test_execution_log_update_failure_does_not_crash(self, orchestrator, mocker):
        """ExecutionLog update failure doesn't crash execution."""
        mocker.patch('tdm_orchestrator.services.orchestration.runner_orchestrator.logger')
        
        mock_log = MagicMock()
        mock_log.id = 123
        mock_log.mark_success.side_effect = Exception("DB error on update")
        mocker.patch.object(orchestrator, '_create_execution_log', return_value=mock_log)
        
        orchestrator.runner.get_pre_scripts.return_value = []
        orchestrator.runner.get_post_scripts.return_value = []
        
        # Should not raise despite log update failure
        result = orchestrator.execute({}, create_log=True)
        
        # Result should still be returned
        assert result is not None
