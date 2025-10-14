from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, TextAreaField, IntegerField, DateField, FileField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from flask_wtf import FlaskForm


class LoginForm(FlaskForm):
    staff_id = StringField('Staff ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class LogoutForm(FlaskForm):
    reason = TextAreaField(
        'Reason for Logging Out Please',
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

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class LearnerBioDataForm(FlaskForm):
    admission_no = StringField('Admission No', validators=[DataRequired(), Length(max=20)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    
    # Updated grade field as dropdown
    grade = SelectField(
        'Grade',
        choices=[
            ('PlayGroup', 'PlayGroup'),
            ('PP1', 'PP1'),
            ('PP2', 'PP2')
        ] + [(f'Grade {i}', f'Grade {i}') for i in range(1, 10)],
        validators=[DataRequired()]
    )

    parent_name = StringField("Parent/Guardian Name", validators=[Optional(), Length(max=100)])
    parent_phone = StringField("Parent Phone", validators=[Optional(), Length(max=20)])
    address = StringField("Address", validators=[Optional(), Length(max=200)])
    medical_conditions = StringField("Medical Conditions", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Add Learner")
