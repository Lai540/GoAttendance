from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    staff_id = StringField('Staff ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class LogoutForm(FlaskForm):
    reason = SelectField('Logout Reason', choices=[
        ('Left early', 'Left early'),
        ('Sick', 'Sick'),
        ('Personal', 'Personal'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField('Logout')

class FirstTimeRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_class_teacher = BooleanField('Are you a class teacher?')
    grade_assigned = SelectField('Grade Assigned', choices=[
        ('', 'Select Grade'),
        ('Playgroup', 'Playgroup'), ('PP1', 'PP1'), ('PP2', 'PP2'),
        ('Grade 1','Grade 1'), ('Grade 2','Grade 2'), ('Grade 3','Grade 3'),
        ('Grade 4','Grade 4'), ('Grade 5','Grade 5'), ('Grade 6','Grade 6'),
        ('Grade 7','Grade 7'), ('Grade 8','Grade 8'), ('Grade 9','Grade 9')
    ])
    subjects = StringField('Subjects you teach (comma separated)', validators=[DataRequired()])
    syllabus_coverage = TextAreaField('Syllabus coverage (optional)')
    submit = SubmitField('Complete Registration')
