class Calculadora:
    """Clase que implementa operaciones matemáticas básicas."""

    def sumar(self, a, b):
        """Devuelve la suma de a y b."""
        return a + b

    def restar(self, a, b):
        """Devuelve la resta de a y b."""
        return a - b

    def multiplicar(self, a, b):
        """Devuelve la multiplicación de a y b."""
        return a * b

    def dividir(self, a, b):
        """Devuelve la división de a entre b."""
        if b == 0:
            raise ValueError("No se puede dividir entre cero")
        return a / b


if __name__ == "__main__":
    calc = Calculadora()

    print("Suma:", calc.sumar(10, 5))
    print("Resta:", calc.restar(10, 5))
    print("Multiplicación:", calc.multiplicar(10, 5))
    print("División:", calc.dividir(10, 5))
