class CompilerValidator:

    def validate(self, canvas):

        errors = []

        warnings = []

        if len(canvas.nodes) == 0:

            errors.append("Builder graph is empty.")

        return {

            "valid": len(errors) == 0,

            "errors": errors,

            "warnings": warnings

        }