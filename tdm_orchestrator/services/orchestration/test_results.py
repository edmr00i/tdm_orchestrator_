"""
Tests for orchestration results dataclasses.

Covers:
- StepResult: Dataclass for individual step execution results
- RunnerExecutionResult: Dataclass for complete runner execution results

Test scenarios:
- Initialization with required/optional fields
- Default values
- Property calculations (counts, totals, failures)
- Methods (add_pre_result, add_post_result, to_dict)
- Edge cases (empty lists, all success, all failure, mixed)
"""

import pytest

from tdm_orchestrator.services.orchestration.results import (
    StepResult,
    RunnerExecutionResult,
)


# =====================
# Fixtures
# =====================

@pytest.fixture
def step_result_success():
    """Creates a successful StepResult."""
    return StepResult(
        script_name="test_script",
        script_reference="REF001",
        step_type="pre",
        order=1,
        success=True,
        duration_ms=100,
    )


@pytest.fixture
def step_result_failure():
    """Creates a failed StepResult."""
    return StepResult(
        script_name="failing_script",
        script_reference="REF002",
        step_type="post",
        order=2,
        success=False,
        duration_ms=50,
        error_message="SQL syntax error",
        rows_affected=0,
    )


@pytest.fixture
def step_result_with_rows():
    """Creates a StepResult with rows_affected."""
    return StepResult(
        script_name="insert_script",
        script_reference="REF003",
        step_type="pre",
        order=1,
        success=True,
        duration_ms=200,
        rows_affected=42,
    )


@pytest.fixture
def runner_result_empty():
    """Creates an empty RunnerExecutionResult."""
    return RunnerExecutionResult(
        runner_id=1,
        runner_name="test_runner",
    )


@pytest.fixture
def runner_result_with_scripts(step_result_success, step_result_failure):
    """Creates a RunnerExecutionResult with pre and post scripts."""
    result = RunnerExecutionResult(
        runner_id=1,
        runner_name="test_runner",
        execution_log_id=123,
        total_duration_ms=500,
    )
    result.add_pre_result(step_result_success)
    result.add_post_result(step_result_failure)
    return result


# =====================
# StepResult Initialization Tests
# =====================

class TestStepResultInit:
    """Tests for StepResult initialization."""

    def test_creates_with_required_fields(self):
        """Creates StepResult with all required fields."""
        result = StepResult(
            script_name="my_script",
            script_reference="REF123",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=150,
        )
        
        assert result.script_name == "my_script"
        assert result.script_reference == "REF123"
        assert result.step_type == "pre"
        assert result.order == 1
        assert result.success is True
        assert result.duration_ms == 150

    def test_default_error_message_is_none(self):
        """Default error_message is None."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=100,
        )
        
        assert result.error_message is None

    def test_default_rows_affected_is_none(self):
        """Default rows_affected is None."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=100,
        )
        
        assert result.rows_affected is None

    def test_creates_with_error_message(self):
        """Creates StepResult with error_message."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="post",
            order=2,
            success=False,
            duration_ms=50,
            error_message="Connection timeout",
        )
        
        assert result.error_message == "Connection timeout"

    def test_creates_with_rows_affected(self):
        """Creates StepResult with rows_affected."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=100,
            rows_affected=10,
        )
        
        assert result.rows_affected == 10

    def test_creates_with_all_fields(self):
        """Creates StepResult with all fields including optional ones."""
        result = StepResult(
            script_name="full_script",
            script_reference="FULL_REF",
            step_type="post",
            order=5,
            success=False,
            duration_ms=999,
            error_message="Full error",
            rows_affected=100,
        )
        
        assert result.script_name == "full_script"
        assert result.script_reference == "FULL_REF"
        assert result.step_type == "post"
        assert result.order == 5
        assert result.success is False
        assert result.duration_ms == 999
        assert result.error_message == "Full error"
        assert result.rows_affected == 100

    def test_step_type_pre(self):
        """Accepts 'pre' as step_type."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=100,
        )
        
        assert result.step_type == "pre"

    def test_step_type_post(self):
        """Accepts 'post' as step_type."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="post",
            order=1,
            success=True,
            duration_ms=100,
        )
        
        assert result.step_type == "post"

    def test_order_zero(self):
        """Accepts zero as order value."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="pre",
            order=0,
            success=True,
            duration_ms=100,
        )
        
        assert result.order == 0

    def test_duration_ms_zero(self):
        """Accepts zero as duration_ms value."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=0,
        )
        
        assert result.duration_ms == 0

    def test_rows_affected_zero(self):
        """Accepts zero as rows_affected value."""
        result = StepResult(
            script_name="script",
            script_reference="REF",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=100,
            rows_affected=0,
        )
        
        assert result.rows_affected == 0

    def test_empty_strings(self):
        """Accepts empty strings for string fields."""
        result = StepResult(
            script_name="",
            script_reference="",
            step_type="",
            order=1,
            success=True,
            duration_ms=100,
            error_message="",
        )
        
        assert result.script_name == ""
        assert result.script_reference == ""
        assert result.step_type == ""
        assert result.error_message == ""


# =====================
# StepResult.to_dict Tests
# =====================

class TestStepResultToDict:
    """Tests for StepResult.to_dict method."""

    def test_returns_dict(self, step_result_success):
        """Returns a dictionary."""
        result = step_result_success.to_dict()
        
        assert isinstance(result, dict)

    def test_contains_all_keys(self, step_result_success):
        """Dictionary contains all expected keys."""
        result = step_result_success.to_dict()
        
        expected_keys = {
            'script_name',
            'script_reference',
            'step_type',
            'order',
            'success',
            'duration_ms',
            'error',
            'rows_affected',
        }
        assert set(result.keys()) == expected_keys

    def test_maps_error_message_to_error_key(self, step_result_failure):
        """Maps error_message attribute to 'error' key."""
        result = step_result_failure.to_dict()
        
        assert 'error' in result
        assert result['error'] == "SQL syntax error"
        assert 'error_message' not in result

    def test_success_result_values(self, step_result_success):
        """Correct values for successful result."""
        result = step_result_success.to_dict()
        
        assert result['script_name'] == "test_script"
        assert result['script_reference'] == "REF001"
        assert result['step_type'] == "pre"
        assert result['order'] == 1
        assert result['success'] is True
        assert result['duration_ms'] == 100
        assert result['error'] is None
        assert result['rows_affected'] is None

    def test_failure_result_values(self, step_result_failure):
        """Correct values for failed result."""
        result = step_result_failure.to_dict()
        
        assert result['script_name'] == "failing_script"
        assert result['script_reference'] == "REF002"
        assert result['step_type'] == "post"
        assert result['order'] == 2
        assert result['success'] is False
        assert result['duration_ms'] == 50
        assert result['error'] == "SQL syntax error"
        assert result['rows_affected'] == 0

    def test_result_with_rows_affected(self, step_result_with_rows):
        """Correct rows_affected value in dictionary."""
        result = step_result_with_rows.to_dict()
        
        assert result['rows_affected'] == 42

    def test_returns_new_dict_each_call(self, step_result_success):
        """Returns new dictionary instance each call."""
        result1 = step_result_success.to_dict()
        result2 = step_result_success.to_dict()
        
        assert result1 == result2
        assert result1 is not result2

    def test_dict_is_serializable(self, step_result_success):
        """Dictionary values are JSON-serializable types."""
        result = step_result_success.to_dict()
        
        # All values should be primitive types
        for value in result.values():
            assert isinstance(value, (str, int, bool, type(None)))


# =====================
# RunnerExecutionResult Initialization Tests
# =====================

class TestRunnerExecutionResultInit:
    """Tests for RunnerExecutionResult initialization."""

    def test_creates_with_required_fields(self):
        """Creates RunnerExecutionResult with required fields only."""
        result = RunnerExecutionResult(
            runner_id=42,
            runner_name="my_runner",
        )
        
        assert result.runner_id == 42
        assert result.runner_name == "my_runner"

    def test_default_execution_log_id_is_none(self):
        """Default execution_log_id is None."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        
        assert result.execution_log_id is None

    def test_default_overall_success_is_true(self):
        """Default overall_success is True."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        
        assert result.overall_success is True

    def test_default_total_duration_ms_is_zero(self):
        """Default total_duration_ms is 0."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        
        assert result.total_duration_ms == 0

    def test_default_pre_scripts_is_empty_list(self):
        """Default pre_scripts is empty list."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        
        assert result.pre_scripts == []
        assert isinstance(result.pre_scripts, list)

    def test_default_post_scripts_is_empty_list(self):
        """Default post_scripts is empty list."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        
        assert result.post_scripts == []
        assert isinstance(result.post_scripts, list)

    def test_default_error_message_is_none(self):
        """Default error_message is None."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        
        assert result.error_message is None

    def test_creates_with_all_fields(self):
        """Creates RunnerExecutionResult with all fields."""
        result = RunnerExecutionResult(
            runner_id=99,
            runner_name="full_runner",
            execution_log_id=456,
            overall_success=False,
            total_duration_ms=5000,
            error_message="Global error",
        )
        
        assert result.runner_id == 99
        assert result.runner_name == "full_runner"
        assert result.execution_log_id == 456
        assert result.overall_success is False
        assert result.total_duration_ms == 5000
        assert result.error_message == "Global error"

    def test_pre_scripts_default_factory_creates_new_list(self):
        """Each instance gets its own pre_scripts list."""
        result1 = RunnerExecutionResult(runner_id=1, runner_name="runner1")
        result2 = RunnerExecutionResult(runner_id=2, runner_name="runner2")
        
        result1.pre_scripts.append("item")
        
        assert len(result1.pre_scripts) == 1
        assert len(result2.pre_scripts) == 0

    def test_post_scripts_default_factory_creates_new_list(self):
        """Each instance gets its own post_scripts list."""
        result1 = RunnerExecutionResult(runner_id=1, runner_name="runner1")
        result2 = RunnerExecutionResult(runner_id=2, runner_name="runner2")
        
        result1.post_scripts.append("item")
        
        assert len(result1.post_scripts) == 1
        assert len(result2.post_scripts) == 0


# =====================
# RunnerExecutionResult.pre_success_count Tests
# =====================

class TestPreSuccessCount:
    """Tests for RunnerExecutionResult.pre_success_count property."""

    def test_returns_zero_for_empty_pre_scripts(self, runner_result_empty):
        """Returns 0 when pre_scripts is empty."""
        count = runner_result_empty.pre_success_count
        
        assert count == 0

    def test_counts_all_successful_pre_scripts(self, step_result_success):
        """Counts all successful pre scripts."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.pre_scripts = [
            step_result_success,
            StepResult("s2", "R2", "pre", 2, True, 100),
            StepResult("s3", "R3", "pre", 3, True, 100),
        ]
        
        assert result.pre_success_count == 3

    def test_excludes_failed_pre_scripts(self, step_result_success, step_result_failure):
        """Excludes failed scripts from count."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        # Create a pre-type failure
        pre_failure = StepResult("fail", "RF", "pre", 2, False, 50, "error")
        result.pre_scripts = [step_result_success, pre_failure]
        
        assert result.pre_success_count == 1

    def test_returns_zero_when_all_failed(self):
        """Returns 0 when all pre scripts failed."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.pre_scripts = [
            StepResult("f1", "R1", "pre", 1, False, 50, "error1"),
            StepResult("f2", "R2", "pre", 2, False, 50, "error2"),
        ]
        
        assert result.pre_success_count == 0


# =====================
# RunnerExecutionResult.post_success_count Tests
# =====================

class TestPostSuccessCount:
    """Tests for RunnerExecutionResult.post_success_count property."""

    def test_returns_zero_for_empty_post_scripts(self, runner_result_empty):
        """Returns 0 when post_scripts is empty."""
        count = runner_result_empty.post_success_count
        
        assert count == 0

    def test_counts_all_successful_post_scripts(self):
        """Counts all successful post scripts."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.post_scripts = [
            StepResult("s1", "R1", "post", 1, True, 100),
            StepResult("s2", "R2", "post", 2, True, 100),
        ]
        
        assert result.post_success_count == 2

    def test_excludes_failed_post_scripts(self):
        """Excludes failed scripts from count."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.post_scripts = [
            StepResult("s1", "R1", "post", 1, True, 100),
            StepResult("f1", "RF", "post", 2, False, 50, "error"),
            StepResult("s2", "R2", "post", 3, True, 100),
        ]
        
        assert result.post_success_count == 2

    def test_returns_zero_when_all_failed(self):
        """Returns 0 when all post scripts failed."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.post_scripts = [
            StepResult("f1", "R1", "post", 1, False, 50, "error1"),
        ]
        
        assert result.post_success_count == 0


# =====================
# RunnerExecutionResult.total_scripts Tests
# =====================

class TestTotalScripts:
    """Tests for RunnerExecutionResult.total_scripts property."""

    def test_returns_zero_for_empty_result(self, runner_result_empty):
        """Returns 0 when both lists are empty."""
        total = runner_result_empty.total_scripts
        
        assert total == 0

    def test_counts_only_pre_scripts(self, step_result_success):
        """Counts pre scripts when post is empty."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.pre_scripts = [step_result_success, step_result_success]
        
        assert result.total_scripts == 2

    def test_counts_only_post_scripts(self, step_result_success):
        """Counts post scripts when pre is empty."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.post_scripts = [step_result_success]
        
        assert result.total_scripts == 1

    def test_counts_both_pre_and_post(self, step_result_success, step_result_failure):
        """Counts combined pre and post scripts."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.pre_scripts = [step_result_success, step_result_success]
        result.post_scripts = [step_result_failure]
        
        assert result.total_scripts == 3

    def test_includes_both_success_and_failure(self, step_result_success, step_result_failure):
        """Counts both successful and failed scripts."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.pre_scripts = [step_result_success, step_result_failure]
        
        assert result.total_scripts == 2


# =====================
# RunnerExecutionResult.failed_scripts Tests
# =====================

class TestFailedScripts:
    """Tests for RunnerExecutionResult.failed_scripts property."""

    def test_returns_empty_list_when_no_scripts(self, runner_result_empty):
        """Returns empty list when no scripts exist."""
        failed = runner_result_empty.failed_scripts
        
        assert failed == []

    def test_returns_empty_list_when_all_success(self, step_result_success):
        """Returns empty list when all scripts succeeded."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.pre_scripts = [step_result_success]
        result.post_scripts = [
            StepResult("post1", "RP1", "post", 1, True, 100)
        ]
        
        assert result.failed_scripts == []

    def test_returns_failed_pre_scripts(self, step_result_success):
        """Returns failed pre scripts."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        pre_failure = StepResult("pre_fail", "RPF", "pre", 1, False, 50, "error")
        result.pre_scripts = [step_result_success, pre_failure]
        
        failed = result.failed_scripts
        
        assert len(failed) == 1
        assert failed[0].script_name == "pre_fail"

    def test_returns_failed_post_scripts(self, step_result_failure):
        """Returns failed post scripts."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.post_scripts = [step_result_failure]
        
        failed = result.failed_scripts
        
        assert len(failed) == 1
        assert failed[0].script_name == "failing_script"

    def test_returns_combined_failed_from_pre_and_post(self):
        """Returns failed scripts from both pre and post."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        pre_failure = StepResult("pre_fail", "RPF", "pre", 1, False, 50, "err1")
        post_failure = StepResult("post_fail", "RPF2", "post", 1, False, 50, "err2")
        result.pre_scripts = [pre_failure]
        result.post_scripts = [post_failure]
        
        failed = result.failed_scripts
        
        assert len(failed) == 2
        assert failed[0].script_name == "pre_fail"
        assert failed[1].script_name == "post_fail"

    def test_preserves_order_pre_then_post(self):
        """Failed scripts maintain order: pre scripts first, then post."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        pre_fail1 = StepResult("pre1", "R1", "pre", 1, False, 50, "e1")
        pre_fail2 = StepResult("pre2", "R2", "pre", 2, False, 50, "e2")
        post_fail = StepResult("post1", "R3", "post", 1, False, 50, "e3")
        result.pre_scripts = [pre_fail1, pre_fail2]
        result.post_scripts = [post_fail]
        
        failed = result.failed_scripts
        
        assert [f.script_name for f in failed] == ["pre1", "pre2", "post1"]

    def test_returns_list_type(self, step_result_failure):
        """Returns a list."""
        result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        result.pre_scripts = [step_result_failure]
        
        failed = result.failed_scripts
        
        assert isinstance(failed, list)


# =====================
# RunnerExecutionResult.add_pre_result Tests
# =====================

class TestAddPreResult:
    """Tests for RunnerExecutionResult.add_pre_result method."""

    def test_appends_to_pre_scripts(self, runner_result_empty, step_result_success):
        """Appends result to pre_scripts list."""
        runner_result_empty.add_pre_result(step_result_success)
        
        assert len(runner_result_empty.pre_scripts) == 1
        assert runner_result_empty.pre_scripts[0] == step_result_success

    def test_appends_multiple_results(self, runner_result_empty, step_result_success):
        """Appends multiple results in order."""
        second_result = StepResult("s2", "R2", "pre", 2, True, 100)
        
        runner_result_empty.add_pre_result(step_result_success)
        runner_result_empty.add_pre_result(second_result)
        
        assert len(runner_result_empty.pre_scripts) == 2
        assert runner_result_empty.pre_scripts[0] == step_result_success
        assert runner_result_empty.pre_scripts[1] == second_result

    def test_keeps_overall_success_true_for_success(self, runner_result_empty, step_result_success):
        """Keeps overall_success True when adding successful result."""
        assert runner_result_empty.overall_success is True
        
        runner_result_empty.add_pre_result(step_result_success)
        
        assert runner_result_empty.overall_success is True

    def test_sets_overall_success_false_for_failure(self, runner_result_empty):
        """Sets overall_success to False when adding failed result."""
        failure = StepResult("fail", "RF", "pre", 1, False, 50, "error")
        
        runner_result_empty.add_pre_result(failure)
        
        assert runner_result_empty.overall_success is False

    def test_overall_success_stays_false_after_failure(self, runner_result_empty, step_result_success):
        """Overall success stays False after first failure."""
        failure = StepResult("fail", "RF", "pre", 1, False, 50, "error")
        
        runner_result_empty.add_pre_result(failure)
        runner_result_empty.add_pre_result(step_result_success)
        
        assert runner_result_empty.overall_success is False

    def test_does_not_modify_post_scripts(self, runner_result_empty, step_result_success):
        """Does not affect post_scripts list."""
        runner_result_empty.add_pre_result(step_result_success)
        
        assert len(runner_result_empty.post_scripts) == 0


# =====================
# RunnerExecutionResult.add_post_result Tests
# =====================

class TestAddPostResult:
    """Tests for RunnerExecutionResult.add_post_result method."""

    def test_appends_to_post_scripts(self, runner_result_empty, step_result_failure):
        """Appends result to post_scripts list."""
        runner_result_empty.add_post_result(step_result_failure)
        
        assert len(runner_result_empty.post_scripts) == 1
        assert runner_result_empty.post_scripts[0] == step_result_failure

    def test_appends_multiple_results(self, runner_result_empty):
        """Appends multiple results in order."""
        post1 = StepResult("p1", "RP1", "post", 1, True, 100)
        post2 = StepResult("p2", "RP2", "post", 2, True, 100)
        
        runner_result_empty.add_post_result(post1)
        runner_result_empty.add_post_result(post2)
        
        assert len(runner_result_empty.post_scripts) == 2
        assert runner_result_empty.post_scripts[0] == post1
        assert runner_result_empty.post_scripts[1] == post2

    def test_keeps_overall_success_true_for_success(self, runner_result_empty):
        """Keeps overall_success True when adding successful result."""
        success = StepResult("s", "RS", "post", 1, True, 100)
        
        runner_result_empty.add_post_result(success)
        
        assert runner_result_empty.overall_success is True

    def test_sets_overall_success_false_for_failure(self, runner_result_empty, step_result_failure):
        """Sets overall_success to False when adding failed result."""
        runner_result_empty.add_post_result(step_result_failure)
        
        assert runner_result_empty.overall_success is False

    def test_overall_success_stays_false_after_failure(self, runner_result_empty):
        """Overall success stays False after first failure."""
        failure = StepResult("fail", "RF", "post", 1, False, 50, "error")
        success = StepResult("success", "RS", "post", 2, True, 100)
        
        runner_result_empty.add_post_result(failure)
        runner_result_empty.add_post_result(success)
        
        assert runner_result_empty.overall_success is False

    def test_does_not_modify_pre_scripts(self, runner_result_empty, step_result_failure):
        """Does not affect pre_scripts list."""
        runner_result_empty.add_post_result(step_result_failure)
        
        assert len(runner_result_empty.pre_scripts) == 0


# =====================
# RunnerExecutionResult.to_dict Tests
# =====================

class TestRunnerExecutionResultToDict:
    """Tests for RunnerExecutionResult.to_dict method."""

    def test_returns_dict(self, runner_result_empty):
        """Returns a dictionary."""
        result = runner_result_empty.to_dict()
        
        assert isinstance(result, dict)

    def test_contains_all_top_level_keys(self, runner_result_empty):
        """Dictionary contains all expected top-level keys."""
        result = runner_result_empty.to_dict()
        
        expected_keys = {
            'runner_id',
            'runner_name',
            'execution_log_id',
            'overall_success',
            'total_duration_ms',
            'pre_scripts',
            'post_scripts',
            'summary',
            'error_message',
        }
        assert set(result.keys()) == expected_keys

    def test_empty_result_values(self, runner_result_empty):
        """Correct values for empty result."""
        result = runner_result_empty.to_dict()
        
        assert result['runner_id'] == 1
        assert result['runner_name'] == "test_runner"
        assert result['execution_log_id'] is None
        assert result['overall_success'] is True
        assert result['total_duration_ms'] == 0
        assert result['pre_scripts'] == []
        assert result['post_scripts'] == []
        assert result['error_message'] is None

    def test_summary_for_empty_result(self, runner_result_empty):
        """Summary values for empty result."""
        result = runner_result_empty.to_dict()
        
        summary = result['summary']
        assert summary['total'] == 0
        assert summary['pre_success'] == 0
        assert summary['post_success'] == 0
        assert summary['failed'] == 0

    def test_pre_scripts_contains_step_dicts(self, runner_result_with_scripts):
        """pre_scripts contains StepResult.to_dict() outputs."""
        result = runner_result_with_scripts.to_dict()
        
        assert len(result['pre_scripts']) == 1
        assert result['pre_scripts'][0]['script_name'] == "test_script"
        assert result['pre_scripts'][0]['step_type'] == "pre"

    def test_post_scripts_contains_step_dicts(self, runner_result_with_scripts):
        """post_scripts contains StepResult.to_dict() outputs."""
        result = runner_result_with_scripts.to_dict()
        
        assert len(result['post_scripts']) == 1
        assert result['post_scripts'][0]['script_name'] == "failing_script"
        assert result['post_scripts'][0]['step_type'] == "post"

    def test_summary_with_scripts(self, runner_result_with_scripts):
        """Summary values with scripts."""
        result = runner_result_with_scripts.to_dict()
        
        summary = result['summary']
        assert summary['total'] == 2
        assert summary['pre_success'] == 1
        assert summary['post_success'] == 0
        assert summary['failed'] == 1

    def test_overall_success_reflects_failures(self, runner_result_with_scripts):
        """overall_success is False when there are failures."""
        result = runner_result_with_scripts.to_dict()
        
        assert result['overall_success'] is False

    def test_includes_execution_log_id(self, runner_result_with_scripts):
        """Includes execution_log_id when set."""
        result = runner_result_with_scripts.to_dict()
        
        assert result['execution_log_id'] == 123

    def test_includes_total_duration_ms(self, runner_result_with_scripts):
        """Includes total_duration_ms when set."""
        result = runner_result_with_scripts.to_dict()
        
        assert result['total_duration_ms'] == 500

    def test_includes_error_message(self):
        """Includes error_message when set."""
        result = RunnerExecutionResult(
            runner_id=1,
            runner_name="runner",
            error_message="Fatal error occurred",
        )
        
        output = result.to_dict()
        
        assert output['error_message'] == "Fatal error occurred"

    def test_returns_new_dict_each_call(self, runner_result_empty):
        """Returns new dictionary instance each call."""
        result1 = runner_result_empty.to_dict()
        result2 = runner_result_empty.to_dict()
        
        assert result1 == result2
        assert result1 is not result2

    def test_pre_scripts_list_is_new_instance(self, runner_result_with_scripts):
        """pre_scripts in dict is a new list instance."""
        result = runner_result_with_scripts.to_dict()
        
        result['pre_scripts'].append({})
        
        # Should not affect original
        assert len(runner_result_with_scripts.pre_scripts) == 1

    def test_summary_contains_correct_keys(self, runner_result_empty):
        """Summary dictionary contains correct keys."""
        result = runner_result_empty.to_dict()
        
        expected_summary_keys = {'total', 'pre_success', 'post_success', 'failed'}
        assert set(result['summary'].keys()) == expected_summary_keys


# =====================
# Integration Tests
# =====================

class TestResultsIntegration:
    """Integration tests for results dataclasses."""

    def test_full_workflow_success(self):
        """Full workflow with all successful scripts."""
        runner_result = RunnerExecutionResult(
            runner_id=1,
            runner_name="integration_runner",
            execution_log_id=999,
            total_duration_ms=1500,
        )
        
        pre1 = StepResult("pre_1", "PRE1", "pre", 1, True, 100, rows_affected=10)
        pre2 = StepResult("pre_2", "PRE2", "pre", 2, True, 200, rows_affected=20)
        post1 = StepResult("post_1", "POST1", "post", 1, True, 150, rows_affected=5)
        
        runner_result.add_pre_result(pre1)
        runner_result.add_pre_result(pre2)
        runner_result.add_post_result(post1)
        
        output = runner_result.to_dict()
        
        assert output['overall_success'] is True
        assert output['summary']['total'] == 3
        assert output['summary']['pre_success'] == 2
        assert output['summary']['post_success'] == 1
        assert output['summary']['failed'] == 0

    def test_full_workflow_with_failures(self):
        """Full workflow with some failed scripts."""
        runner_result = RunnerExecutionResult(
            runner_id=2,
            runner_name="failing_runner",
            total_duration_ms=800,
        )
        
        pre1 = StepResult("pre_1", "PRE1", "pre", 1, True, 100)
        pre2 = StepResult("pre_2", "PRE2", "pre", 2, False, 50, "PRE error")
        post1 = StepResult("post_1", "POST1", "post", 1, False, 30, "POST error")
        
        runner_result.add_pre_result(pre1)
        runner_result.add_pre_result(pre2)
        runner_result.add_post_result(post1)
        
        output = runner_result.to_dict()
        
        assert output['overall_success'] is False
        assert output['summary']['total'] == 3
        assert output['summary']['pre_success'] == 1
        assert output['summary']['post_success'] == 0
        assert output['summary']['failed'] == 2

    def test_step_result_in_dict_contains_all_info(self):
        """StepResult in to_dict output contains all information."""
        runner_result = RunnerExecutionResult(runner_id=1, runner_name="runner")
        
        step = StepResult(
            script_name="detailed_script",
            script_reference="DETAIL_REF",
            step_type="pre",
            order=5,
            success=True,
            duration_ms=999,
            error_message=None,
            rows_affected=42,
        )
        runner_result.add_pre_result(step)
        
        output = runner_result.to_dict()
        step_dict = output['pre_scripts'][0]
        
        assert step_dict['script_name'] == "detailed_script"
        assert step_dict['script_reference'] == "DETAIL_REF"
        assert step_dict['step_type'] == "pre"
        assert step_dict['order'] == 5
        assert step_dict['success'] is True
        assert step_dict['duration_ms'] == 999
        assert step_dict['error'] is None
        assert step_dict['rows_affected'] == 42


# =====================
# Edge Cases
# =====================

class TestResultsEdgeCases:
    """Edge case tests for results dataclasses."""

    def test_step_result_unicode_in_fields(self):
        """StepResult handles unicode in string fields."""
        step = StepResult(
            script_name="スクリプト",
            script_reference="参照",
            step_type="pre",
            order=1,
            success=False,
            duration_ms=100,
            error_message="Erreur: données invalides 日本語",
        )
        
        result = step.to_dict()
        
        assert result['script_name'] == "スクリプト"
        assert result['error'] == "Erreur: données invalides 日本語"

    def test_runner_result_unicode_in_fields(self):
        """RunnerExecutionResult handles unicode in string fields."""
        result = RunnerExecutionResult(
            runner_id=1,
            runner_name="运行器",
            error_message="エラー発生",
        )
        
        output = result.to_dict()
        
        assert output['runner_name'] == "运行器"
        assert output['error_message'] == "エラー発生"

    def test_very_large_duration_ms(self):
        """Handles very large duration values."""
        step = StepResult(
            script_name="slow",
            script_reference="SLOW",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=999999999,
        )
        
        result = step.to_dict()
        
        assert result['duration_ms'] == 999999999

    def test_very_large_rows_affected(self):
        """Handles very large rows_affected values."""
        step = StepResult(
            script_name="bulk",
            script_reference="BULK",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=100,
            rows_affected=10000000,
        )
        
        result = step.to_dict()
        
        assert result['rows_affected'] == 10000000

    def test_many_scripts_in_runner(self):
        """Handles many scripts in a single runner result."""
        runner_result = RunnerExecutionResult(runner_id=1, runner_name="bulk_runner")
        
        for i in range(100):
            step = StepResult(
                f"script_{i}",
                f"REF_{i}",
                "pre" if i % 2 == 0 else "post",
                i,
                i % 3 != 0,  # Some failures
                100,
            )
            if step.step_type == "pre":
                runner_result.add_pre_result(step)
            else:
                runner_result.add_post_result(step)
        
        output = runner_result.to_dict()
        
        assert output['summary']['total'] == 100
        assert len(output['pre_scripts']) + len(output['post_scripts']) == 100

    def test_negative_duration_ms(self):
        """Handles negative duration (edge case, shouldn't happen)."""
        step = StepResult(
            script_name="negative",
            script_reference="NEG",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=-1,
        )
        
        result = step.to_dict()
        
        assert result['duration_ms'] == -1

    def test_negative_rows_affected(self):
        """Handles negative rows_affected (edge case)."""
        step = StepResult(
            script_name="negative",
            script_reference="NEG",
            step_type="pre",
            order=1,
            success=True,
            duration_ms=100,
            rows_affected=-5,
        )
        
        result = step.to_dict()
        
        assert result['rows_affected'] == -5

    def test_error_message_with_special_characters(self):
        """Handles error message with special characters."""
        step = StepResult(
            script_name="special",
            script_reference="SPEC",
            step_type="pre",
            order=1,
            success=False,
            duration_ms=50,
            error_message="Error: <tag>&amp;'\"\\n\\t",
        )
        
        result = step.to_dict()
        
        assert result['error'] == "Error: <tag>&amp;'\"\\n\\t"

    def test_very_long_error_message(self):
        """Handles very long error message."""
        long_error = "x" * 10000
        step = StepResult(
            script_name="long_error",
            script_reference="LONG",
            step_type="pre",
            order=1,
            success=False,
            duration_ms=50,
            error_message=long_error,
        )
        
        result = step.to_dict()
        
        assert len(result['error']) == 10000


# =====================
# Summary of Covered Cases
# =====================
# StepResult:
# - Initialization with required fields only
# - Initialization with all optional fields
# - Default values (error_message=None, rows_affected=None)
# - Edge cases (zero values, empty strings, unicode)
# - to_dict() returns correct structure
# - to_dict() maps error_message to 'error' key
# - to_dict() returns new dict each call
#
# RunnerExecutionResult:
# - Initialization with required fields only
# - Default values (overall_success=True, empty lists, etc.)
# - Default factory creates separate lists per instance
# - pre_success_count property (empty, all success, mixed, all failed)
# - post_success_count property (empty, all success, mixed, all failed)
# - total_scripts property (empty, pre only, post only, both)
# - failed_scripts property (empty, all success, pre failures, post failures, mixed)
# - add_pre_result appends and updates overall_success
# - add_post_result appends and updates overall_success
# - overall_success stays False after failure
# - to_dict() returns correct structure with all keys
# - to_dict() includes nested StepResult.to_dict() outputs
# - to_dict() summary contains correct counts
# - to_dict() returns new dict/list instances each call
#
# Integration:
# - Full workflow with all successful scripts
# - Full workflow with some failures
# - Step details preserved in to_dict output
#
# Edge cases:
# - Unicode in string fields
# - Very large numeric values
# - Many scripts in single runner
# - Negative values (edge case handling)
# - Special characters in error messages
# - Very long strings