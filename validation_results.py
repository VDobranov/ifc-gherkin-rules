import os
import sys
from pathlib import Path

# Ленивая инициализация Django — только при реальном использовании
_django_initialized = False

def _init_django():
    """Initialize Django only when needed."""
    global _django_initialized
    if _django_initialized:
        return
    
    import django
    from django.core.management import call_command
    
    # @todo importing from random directories is a security hazard, this should be properly passed as a configuration param
    current_script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, str(current_script_dir.parent.parent.parent.parent))

    try:
        import apps.ifc_validation_models as ifc_validation_models
    except:
        import ifc_validation_models

    if ifc_validation_models.__file__ and Path(ifc_validation_models.__file__).parent == current_script_dir / 'ifc_validation_models':
        # we are using our own submodule
        try:
            ifc_validation_models.apps.IfcValidationModelsConfig.name = 'ifc_validation_models'
        except:
            from ifc_validation_models import apps
            apps.IfcValidationModelsConfig.name = 'ifc_validation_models'
        os.environ['DJANGO_SETTINGS_MODULE'] = 'ifc_validation_models.independent_worker_settings'
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.ifc_validation_models.dependent_worker_settings'

    django.setup()
    _django_initialized = True


def _get_validation_classes():
    """Get validation classes with lazy Django initialization."""
    _init_django()
    
    try:
        from apps.ifc_validation_models.models import (
            ValidationOutcome, ModelInstance, ValidationTask
        )
        ValidationOutcomeDjango = ValidationOutcome
        OutcomeSeverity = ValidationOutcome.OutcomeSeverity
        ValidationOutcomeCode = ValidationOutcome.ValidationOutcomeCode
        from apps.ifc_validation_models.dataclass_compat import ValidationOutcome
    except:
        from ifc_validation_models.models import (
            ValidationOutcome, ModelInstance, ValidationTask
        )
        ValidationOutcomeDjango = ValidationOutcome
        OutcomeSeverity = ValidationOutcome.OutcomeSeverity
        ValidationOutcomeCode = ValidationOutcome.ValidationOutcomeCode
        from ifc_validation_models.dataclass_compat import ValidationOutcome
    
    return (ValidationOutcome, ValidationOutcomeDjango, OutcomeSeverity, 
            ValidationOutcomeCode, ModelInstance, ValidationTask)


# Не инициализируем Django при импорте!
# Вызываем _get_validation_classes() только когда нужны классы
ValidationOutcome = None
ValidationOutcomeDjango = None
OutcomeSeverity = None
ValidationOutcomeCode = None
ModelInstance = None
ValidationTask = None


def __getattr__(name):
    """Lazy loading of validation classes."""
    global ValidationOutcome, ValidationOutcomeDjango, OutcomeSeverity, ValidationOutcomeCode, ModelInstance, ValidationTask
    
    if name in ['ValidationOutcome', 'ValidationOutcomeDjango', 'OutcomeSeverity', 
                'ValidationOutcomeCode', 'ModelInstance', 'ValidationTask']:
        if ValidationOutcome is None:
            (ValidationOutcome, ValidationOutcomeDjango, OutcomeSeverity, 
             ValidationOutcomeCode, ModelInstance, ValidationTask) = _get_validation_classes()
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":

    call_command(
        'migrate', interactive=False,
    )

    import ifc_validation_models.models as database
    from django.contrib.auth.models import User

    user = User.objects.filter(username='system').first()

    if not user:
        user = User.objects.create(username='system',
                                   email='system',
                                   password='system')

    database.set_user_context(user)

    model = database.Model.objects.create(
        size=1,
        uploaded_by = user
    )

    validation_request = database.ValidationRequest.objects.create(size=1, model_id = 1)
    validation_task = database.ValidationTask.objects.create(request_id=1)