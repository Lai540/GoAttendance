from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class LoginForm(FlaskForm):
    staff_id = StringField('Staff ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class LogoutForm(FlaskForm):
    reason = TextAreaField(
        'Reason for Logging Out Early',
        validators=[
            DataRequired(message="Please provide a reason."),
            Length(min=5, max=500, message="Reason must be between 5 and 500 characters.")
        ]
    )
    submit = SubmitField('Logout')

class FirstTimeRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_class_teacher = BooleanField('Are you a class teacher?')
    grade_assigned = SelectField(
        'Grade Assigned',
        choices=[('', 'Select Grade'), ('Playgroup', 'Playgroup'), ('PP1', 'PP1'), ('PP2', 'PP2'),
                 ('Grade 1','Grade 1'), ('Grade 2','Grade 2'), ('Grade 3','Grade 3'),
                 ('Grade 4','Grade 4'), ('Grade 5','Grade 5'), ('Grade 6','Grade 6'),
                 ('Grade 7','Grade 7'), ('Grade 8','Grade 8'), ('Grade 9','Grade 9')]
    )
    subjects = StringField('Subjects you teach (comma separated)', validators=[DataRequired()])
    syllabus_coverage = TextAreaField('Syllabus coverage (optional)')
    submit = SubmitField('Complete Registration')

class LearnersDataForm(FlaskForm):
    ecde_girls = IntegerField('ECDE Girls', validators=[DataRequired(), NumberRange(min=0)])
    ecde_boys = IntegerField('ECDE Boys', validators=[DataRequired(), NumberRange(min=0)])
    primary_girls = IntegerField('Primary Girls', validators=[DataRequired(), NumberRange(min=0)])
    primary_boys = IntegerField('Primary Boys', validators=[DataRequired(), NumberRange(min=0)])
    jss_girls = IntegerField('JSS Girls', validators=[DataRequired(), NumberRange(min=0)])
    jss_boys = IntegerField('JSS Boys', validators=[DataRequired(), NumberRange(min=0)])
    total_population = IntegerField('Total Population of Learners', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Learners Data')
