import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculadora import Calculadora


@pytest.fixture
def calc():
    return Calculadora()


class TestSumar:
    def test_sumar_positivos(self, calc):
        assert calc.sumar(2, 3) == 5

    def test_sumar_negativos(self, calc):
        assert calc.sumar(-2, -3) == -5

    def test_sumar_con_cero(self, calc):
        assert calc.sumar(5, 0) == 5


class TestRestar:
    def test_restar_positivos(self, calc):
        assert calc.restar(5, 3) == 2

    def test_restar_resultado_negativo(self, calc):
        assert calc.restar(3, 5) == -2

    def test_restar_con_cero(self, calc):
        assert calc.restar(5, 0) == 5


class TestMultiplicar:
    def test_multiplicar_positivos(self, calc):
        assert calc.multiplicar(4, 3) == 12

    def test_multiplicar_por_cero(self, calc):
        assert calc.multiplicar(4, 0) == 0

    def test_multiplicar_negativos(self, calc):
        assert calc.multiplicar(-2, 3) == -6


class TestDividir:
    def test_dividir_exacta(self, calc):
        assert calc.dividir(10, 5) == 2

    def test_dividir_resultado_flotante(self, calc):
        assert calc.dividir(5, 2) == 2.5

    def test_dividir_entre_cero_lanza_excepcion(self, calc):
        with pytest.raises(ValueError):
            calc.dividir(10, 0)
