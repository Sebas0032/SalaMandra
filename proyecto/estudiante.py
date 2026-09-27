class Student:
    """Un estudiante identificado por codigo."""
    def __init__(self, code, first_name, last_name):
        self.code = code
        self.first_name= first_name
        self.last_name= last_name

    def full_name(self):
        """Devuelve el nombre completo."""
        return f"{self.first_name} {self.last_name}"

