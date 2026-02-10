from django.contrib import admin
from .models import (
    Type,
    Entity,
    DataSource,
    Application,
    SqlScript,
    Runner,
    RunnerStep,
    ExecutionLog,
)

admin.site.register(Type)
admin.site.register(Entity)
admin.site.register(DataSource)
admin.site.register(Application)
admin.site.register(SqlScript)
admin.site.register(Runner)
admin.site.register(RunnerStep)
admin.site.register(ExecutionLog)