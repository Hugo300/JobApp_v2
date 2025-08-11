from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, URLField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL, Optional, ValidationError
from utils.forms import CustomValidators

class JobForm(FlaskForm):
    company = StringField('Company', validators=[DataRequired()])
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description')
    url = URLField('Job URL', validators=[Optional(), URL()])
    office_location = StringField('Office Location', validators=[Optional()], render_kw={"placeholder": "e.g., New York, NY or Remote"})
    country = StringField('Country', validators=[Optional()], render_kw={"placeholder": "e.g., United States"})
    job_mode = SelectField('Job Mode', choices=[('', 'Select job mode')], validators=[Optional()])
    submit = SubmitField('Create Application')

    def __init__(self, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from models import JobMode
        # Add job mode options to the select field
        job_mode_choices = [('', 'Select job mode')]
        job_mode_choices.extend([(mode.value, mode.value) for mode in JobMode])
        self.job_mode.choices = job_mode_choices

    def validate(self, extra_validators=None):
        """Runs all validators and returns True if all pass, or False if any fail."""
        success = super().validate(extra_validators=extra_validators)
        if not success:
            return False

        return True

class LogForm(FlaskForm):
    note = TextAreaField('Note', validators=[DataRequired()], render_kw={"rows": 4, "placeholder": "Enter log details...", "maxlength": "1000"})
    status_change = SelectField('Update Status (Optional)', choices=[('', 'No status change')], validators=[Optional()])
    submit = SubmitField('Add Log')

    def __init__(self, *args, **kwargs):
        super(LogForm, self).__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from models import ApplicationStatus
        # Add status options to the select field
        status_choices = [('', 'No status change')]
        status_choices.extend([(status.value, status.value) for status in ApplicationStatus])
        self.status_change.choices = status_choices

    def validate_note(self, field):
        """Custom validation for note field"""
        if len(field.data.strip()) < 5:
            raise ValidationError('Note must be at least 5 characters long.')
        if len(field.data) > 1000:
            raise ValidationError('Note cannot exceed 1000 characters.')

class QuickLogForm(FlaskForm):
    """Simplified form for quick log entries"""
    note = TextAreaField('Quick Note', validators=[DataRequired()], render_kw={"rows": 2, "placeholder": "Add a quick note...", "maxlength": "500"})
    submit = SubmitField('Add Quick Log')
