from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField
from wtforms.validators import InputRequired


class AbstractForm(FlaskForm):
    hidden_tag = HiddenField()


class LoginForm(AbstractForm):
    username =   StringField(render_kw  = {"placeholder": "Enter your username"},
                             validators = [InputRequired()])
    password = PasswordField(render_kw  = {"placeholder": "Enter your password"},
                             validators = [InputRequired()])


class CreateChatForm(AbstractForm):
    title = StringField(render_kw  = {"placeholder": "Enter chat title"},
                        validators = [InputRequired()])
