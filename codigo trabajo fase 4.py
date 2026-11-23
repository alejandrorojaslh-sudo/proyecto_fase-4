"""
Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación 213023 - Fase 4
Implementación educativa en Python, sin base de datos.
La información se administra mediante objetos y listas; los eventos y errores
se registran en el archivo software_fj.log.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging


# ---------------------------------------------------------------------
# CONFIGURACIÓN DEL ARCHIVO DE REGISTRO (LOGS)
# ---------------------------------------------------------------------

logging.basicConfig(
    filename="software_fj.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)


# ---------------------------------------------------------------------
# EXCEPCIONES PERSONALIZADAS
# ---------------------------------------------------------------------

class ErrorSistema(Exception):
    """Excepción base para los errores propios del sistema."""


class DatoInvalidoError(ErrorSistema):
    """Se utiliza cuando un dato ingresado no cumple las validaciones."""


class ServicioNoDisponibleError(ErrorSistema):
    """Se utiliza cuando un servicio no está disponible."""


class ReservaError(ErrorSistema):
    """Se utiliza cuando una reserva no puede procesarse."""


# ---------------------------------------------------------------------
# CLASE ABSTRACTA GENERAL
# ---------------------------------------------------------------------

class Entidad(ABC):
    def __init__(self, identificador):
        if not identificador:
            raise DatoInvalidoError("El identificador no puede estar vacío.")
        self._identificador = identificador

    @property
    def identificador(self):
        return self._identificador

    @abstractmethod
    def describir(self):
        """Cada entidad debe implementar su propia descripción."""


# ---------------------------------------------------------------------
# CLASE CLIENTE
# ---------------------------------------------------------------------

class Cliente(Entidad):
    def __init__(self, identificador, nombre, correo, telefono):
        super().__init__(identificador)

        if not isinstance(nombre, str) or len(nombre.strip()) < 2:
            raise DatoInvalidoError("El nombre debe tener al menos dos caracteres.")
        if "@" not in correo or "." not in correo:
            raise DatoInvalidoError("El correo electrónico no tiene un formato válido.")
        if not str(telefono).isdigit() or len(str(telefono)) < 7:
            raise DatoInvalidoError("El teléfono debe contener al menos siete dígitos.")

        self.__nombre = nombre.strip()
        self.__correo = correo.strip()
        self.__telefono = str(telefono)

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    def describir(self):
        return f"Cliente {self.identificador}: {self.__nombre} ({self.__correo})"


# ---------------------------------------------------------------------
# CLASE ABSTRACTA SERVICIO Y SERVICIOS ESPECIALIZADOS
# ---------------------------------------------------------------------

class Servicio(Entidad, ABC):
    def __init__(self, identificador, nombre, tarifa, disponible=True):
        super().__init__(identificador)
        if not isinstance(tarifa, (int, float)) or tarifa <= 0:
            raise DatoInvalidoError("La tarifa debe ser un número mayor que cero.")
        self.nombre = nombre
        self.tarifa = float(tarifa)
        self.disponible = disponible

    @abstractmethod
    def calcular_costo(self, cantidad=1, descuento=0, impuesto=0):
        pass

    @abstractmethod
    def validar_parametros(self, cantidad):
        pass

    def describir(self):
        estado = "Disponible" if self.disponible else "No disponible"
        return f"{self.nombre} - ${self.tarifa:.2f} por unidad - {estado}"


class ReservaSala(Servicio):
    def __init__(self, identificador, tarifa_hora, disponible=True):
        super().__init__(identificador, "Reserva de sala", tarifa_hora, disponible)

    def validar_parametros(self, cantidad):
        if not isinstance(cantidad, (int, float)) or cantidad <= 0:
            raise DatoInvalidoError("La duración de la sala debe ser mayor que cero.")

    def calcular_costo(self, cantidad=1, descuento=0, impuesto=0):
        self.validar_parametros(cantidad)
        subtotal = self.tarifa * cantidad
        return subtotal * (1 - descuento) * (1 + impuesto)


class AlquilerEquipo(Servicio):
    def __init__(self, identificador, tarifa_dia, disponible=True):
        super().__init__(identificador, "Alquiler de equipos", tarifa_dia, disponible)

    def validar_parametros(self, cantidad):
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise DatoInvalidoError("La cantidad de días debe ser un entero positivo.")

    def calcular_costo(self, cantidad=1, descuento=0, impuesto=0):
        self.validar_parametros(cantidad)
        subtotal = self.tarifa * cantidad
        return subtotal * (1 - descuento) * (1 + impuesto)


class Asesoria(Servicio):
    def __init__(self, identificador, tarifa_hora, disponible=True):
        super().__init__(identificador, "Asesoría especializada", tarifa_hora, disponible)

    def validar_parametros(self, cantidad):
        if not isinstance(cantidad, (int, float)) or cantidad <= 0:
            raise DatoInvalidoError("Las horas de asesoría deben ser mayores que cero.")

    def calcular_costo(self, cantidad=1, descuento=0, impuesto=0):
        self.validar_parametros(cantidad)
        subtotal = self.tarifa * cantidad
        return subtotal * (1 - descuento) * (1 + impuesto)


# ---------------------------------------------------------------------
# CLASE RESERVA
# ---------------------------------------------------------------------

class Reserva(Entidad):
    def __init__(self, identificador, cliente, servicio, cantidad):
        super().__init__(identificador)
        if not isinstance(cliente, Cliente):
            raise DatoInvalidoError("Debe seleccionar un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("Debe seleccionar un servicio válido.")
        servicio.validar_parametros(cantidad)

        self.cliente = cliente
        self.servicio = servicio
        self.cantidad = cantidad
        self.estado = "Pendiente"
        self.costo = 0.0

    # Método de costo con parámetros opcionales: permite calcular con o sin
    # descuento e impuesto, simulando distintas variantes de sobrecarga.
    def procesar(self, descuento=0, impuesto=0):
        try:
            if not self.servicio.disponible:
                raise ServicioNoDisponibleError(
                    f"El servicio {self.servicio.nombre} no está disponible."
                )
            if not 0 <= descuento < 1:
                raise DatoInvalidoError("El descuento debe estar entre 0 y 1.")
            if not 0 <= impuesto < 1:
                raise DatoInvalidoError("El impuesto debe estar entre 0 y 1.")

            self.costo = self.servicio.calcular_costo(
                self.cantidad, descuento, impuesto
            )
            self.estado = "Confirmada"
            logging.info("Reserva %s confirmada. Cliente: %s. Total: %.2f",
                         self.identificador, self.cliente.nombre, self.costo)
            return self.costo

        except (ServicioNoDisponibleError, DatoInvalidoError) as error:
            self.estado = "Fallida"
            logging.error("Error al procesar reserva %s: %s",
                          self.identificador, error)
            raise ReservaError("No fue posible procesar la reserva.") from error

        else:
            # La cláusula else de try/except se ilustra en la función
            # registrar_operacion del gestor.
            pass

    def cancelar(self):
        if self.estado != "Confirmada":
            raise ReservaError("Solo se puede cancelar una reserva confirmada.")
        self.estado = "Cancelada"
        logging.info("Reserva %s cancelada.", self.identificador)

    def describir(self):
        return (f"Reserva {self.identificador} | {self.cliente.nombre} | "
                f"{self.servicio.nombre} | Estado: {self.estado} | "
                f"Total: ${self.costo:.2f}")


# ---------------------------------------------------------------------
# GESTOR DEL SISTEMA: ADMINISTRA LISTAS EN MEMORIA
# ---------------------------------------------------------------------

class GestorSoftwareFJ:
    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    def registrar_cliente(self, cliente):
        if any(c.identificador == cliente.identificador for c in self.clientes):
            raise DatoInvalidoError("Ya existe un cliente con ese identificador.")
        self.clientes.append(cliente)
        logging.info("Cliente registrado: %s", cliente.describir())
        return cliente

    def registrar_servicio(self, servicio):
        if any(s.identificador == servicio.identificador for s in self.servicios):
            raise DatoInvalidoError("Ya existe un servicio con ese identificador.")
        self.servicios.append(servicio)
        logging.info("Servicio registrado: %s", servicio.describir())
        return servicio

    def crear_reserva(self, identificador, id_cliente, id_servicio, cantidad):
        try:
            cliente = next(c for c in self.clientes
                           if c.identificador == id_cliente)
            servicio = next(s for s in self.servicios
                            if s.identificador == id_servicio)
        except StopIteration as error:
            logging.exception("No se encontró el cliente o servicio solicitado.")
            raise ReservaError("El cliente o el servicio no existe.") from error

        reserva = Reserva(identificador, cliente, servicio, cantidad)
        self.reservas.append(reserva)
        logging.info("Reserva creada: %s", identificador)
        return reserva

    def registrar_operacion(self, descripcion, accion):
        """Ejemplo de try/except/else/finally para controlar operaciones."""
        print(f"\nOPERACIÓN: {descripcion}")
        try:
            resultado = accion()
        except ErrorSistema as error:
            print(f"ERROR CONTROLADO: {error}")
            logging.error("Operación '%s' fallida: %s", descripcion, error)
            return None
        else:
            print("Resultado: operación realizada correctamente.")
            return resultado
        finally:
            print("Fin de la operación.")

    def mostrar_estado(self):
        print("\n========== CLIENTES ==========")
        for cliente in self.clientes:
            print(cliente.describir())

        print("\n========== SERVICIOS ==========")
        for servicio in self.servicios:
            print(servicio.describir())

        print("\n========== RESERVAS ==========")
        for reserva in self.reservas:
            print(reserva.describir())


# ---------------------------------------------------------------------
# DEMOSTRACIÓN DE 10 O MÁS OPERACIONES
# ---------------------------------------------------------------------

def ejecutar_pruebas():
    sistema = GestorSoftwareFJ()

    print("SISTEMA INTEGRAL SOFTWARE FJ")
    print("Demostración de operaciones y manejo de excepciones")

    # 1. Registro válido de cliente
    sistema.registrar_operacion(
        "1. Registrar cliente válido",
        lambda: sistema.registrar_cliente(
            Cliente("C001", "Ana Pérez", "ana@email.com", "3001234567")
        )
    )

    # 2. Registro de otro cliente válido
    sistema.registrar_operacion(
        "2. Registrar segundo cliente",
        lambda: sistema.registrar_cliente(
            Cliente("C002", "Carlos Gómez", "carlos@email.com", "3107654321")
        )
    )

    # 3. Registro inválido de cliente: correo incorrecto
    sistema.registrar_operacion(
        "3. Intentar registrar cliente con correo inválido",
        lambda: sistema.registrar_cliente(
            Cliente("C003", "Luis Díaz", "correo_invalido", "3112223344")
        )
    )

    # 4. Crear servicio de reserva de sala
    sistema.registrar_operacion(
        "4. Crear servicio de sala",
        lambda: sistema.registrar_servicio(
            ReservaSala("S001", 50000)
        )
    )

    # 5. Crear servicio de alquiler de equipos
    sistema.registrar_operacion(
        "5. Crear servicio de alquiler de equipos",
        lambda: sistema.registrar_servicio(
            AlquilerEquipo("S002", 80000)
        )
    )

    # 6. Crear servicio de asesoría
    sistema.registrar_operacion(
        "6. Crear servicio de asesoría",
        lambda: sistema.registrar_servicio(
            Asesoria("S003", 60000)
        )
    )

    # 7. Intentar crear servicio con tarifa incorrecta
    sistema.registrar_operacion(
        "7. Intentar crear servicio con tarifa negativa",
        lambda: sistema.registrar_servicio(
            ReservaSala("S004", -10000)
        )
    )

    # 8. Crear y confirmar reserva válida
    def reserva_valida():
        reserva = sistema.crear_reserva("R001", "C001", "S001", 2)
        total = reserva.procesar(descuento=0.10, impuesto=0.19)
        print(f"Reserva confirmada. Total a pagar: ${total:,.2f}")
        return reserva

    sistema.registrar_operacion("8. Crear y confirmar reserva válida",
                                reserva_valida)

    # 9. Intentar reservar un servicio inexistente
    sistema.registrar_operacion(
        "9. Intentar reservar servicio inexistente",
        lambda: sistema.crear_reserva("R002", "C001", "S999", 1)
    )

    # 10. Intentar crear reserva con duración inválida
    sistema.registrar_operacion(
        "10. Intentar reserva con duración cero",
        lambda: sistema.crear_reserva("R003", "C002", "S002", 0)
    )

    # 11. Crear y confirmar una asesoría
    def reserva_asesoria():
        reserva = sistema.crear_reserva("R004", "C002", "S003", 1.5)
        total = reserva.procesar()
        print(f"Asesoría confirmada. Total: ${total:,.2f}")
        return reserva

    sistema.registrar_operacion("11. Crear reserva de asesoría",
                                reserva_asesoria)

    # 12. Cancelar reserva confirmada
    def cancelar_reserva():
        reserva = next(r for r in sistema.reservas
                       if r.identificador == "R001")
        reserva.cancelar()
        print("Reserva R001 cancelada.")
        return reserva

    sistema.registrar_operacion("12. Cancelar reserva confirmada",
                                cancelar_reserva)

    # Ejemplo de try/except/finally explícito y encadenamiento:
    print("\nPRUEBA ADICIONAL: encadenamiento de excepciones")
    try:
        try:
            int("dato-no-numerico")
        except ValueError as error_original:
            raise DatoInvalidoError(
                "No se pudo convertir el dato a número."
            ) from error_original
    except DatoInvalidoError as error:
        print(f"Excepción personalizada controlada: {error}")
        logging.exception("Prueba de encadenamiento de excepciones.")

    sistema.mostrar_estado()
    print("\nSe registraron los eventos y errores en software_fj.log")
    print("Fin de la demostración. El programa continúa funcionando.")


if __name__ == "__main__":
    ejecutar_pruebas()
