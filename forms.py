from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class DisponibilitaForm(FlaskForm):
    data = DateField('Data', validators=[DataRequired()])
    ora_inizio = TimeField('Ora Inizio', validators=[DataRequired()])
    ora_fine = TimeField('Ora Fine', validators=[DataRequired()])
    stato = SelectField('Stato', choices=[
        ('disponibile', 'Disponibile'),
        ('occupato', 'Occupato'),
        ('non_disponibile', 'Non Disponibile')
    ], validators=[DataRequired()])
    note = TextAreaField('Note') 