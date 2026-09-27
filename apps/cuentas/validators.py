from django.core.exceptions import ValidationError


class RequisitosInstitucionalesValidator:
    """Exige mayúscula, minúscula y un carácter especial (mockup §4)."""

    def validate(self, password, user=None):
        faltantes = []
        if not any(caracter.isupper() for caracter in password):
            faltantes.append("una letra mayúscula")
        if not any(caracter.islower() for caracter in password):
            faltantes.append("una letra minúscula")
        if not any(not caracter.isalnum() for caracter in password):
            faltantes.append("un carácter especial")
        if faltantes:
            raise ValidationError(
                "La contraseña debe incluir " + ", ".join(faltantes) + ".",
                code="requisitos_institucionales",
            )

    def get_help_text(self):
        return (
            "Debe incluir una letra mayúscula, una minúscula y un carácter especial."
        )
