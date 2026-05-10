import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from functools import wraps

# ==================== Настройка логирования ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bike_rental.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== Пользовательские исключения ====================
class InvalidBikeError(Exception):
    """Выбрасывается, когда велосипед содержит некорректные данные"""
    pass

class PermissionDeniedError(Exception):
    """Выбрасывается, когда у пользователя нет прав доступа"""
    pass

class RentalNotFoundError(Exception):
    """Выбрасывается, когда аренда не найдена"""
    pass

# ==================== Метакласс ====================
class BicycleMeta(type(ABC)):
    """Метакласс, который автоматически регистрирует все подклассы Bicycle"""
    _registry = {}
    
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if name != 'Bicycle' and not getattr(cls, '_abstract', False):
            BicycleMeta._registry[name.lower()] = cls
        return cls
    
    @classmethod
    def get_registry(mcs):
        return mcs._registry

# ==================== Миксины ====================
class LoggingMixin:
    """Миксин, добавляющий функциональность логирования"""
    
    def log_action(self, action: str, details: str = ""):
        """Записать действие с временной меткой"""
        log_msg = f"Действие: {action}"
        if details:
            log_msg += f" | Подробности: {details}"
        logger.info(log_msg)
        return log_msg

class NotificationMixin:
    """Миксин, добавляющий функциональность отправки уведомлений"""
    
    def send_notification(self, message: str, notification_type: str = "info"):
        """Отправить уведомление"""
        type_rus = {
            "info": "инфо",
            "success": "успех",
            "error": "ошибка",
            "warning": "предупреждение"
        }.get(notification_type, notification_type)
        notification_msg = f"[{type_rus.upper()}] {message}"
        logger.info(f"УВЕДОМЛЕНИЕ: {notification_msg}")
        return notification_msg

# ==================== Абстрактный базовый класс ====================
class Bicycle(ABC, LoggingMixin, NotificationMixin, metaclass=BicycleMeta):
    """Абстрактный базовый класс для всех типов велосипедов"""
    
    def __init__(self, bicycle_id: str, model: str, bike_type: str, hourly_rate: float, is_available: bool = True):
        self.__bicycle_id = bicycle_id
        self.__model = model
        self.__type = bike_type
        self.__hourly_rate = hourly_rate
        self.__is_available = is_available
    
    # Геттеры
    def get_bicycle_id(self) -> str:
        return self.__bicycle_id
    
    def get_model(self) -> str:
        return self.__model
    
    def get_type(self) -> str:
        return self.__type
    
    def get_hourly_rate(self) -> float:
        return self.__hourly_rate
    
    def is_available(self) -> bool:
        return self.__is_available
    
    # Сеттеры
    def set_bicycle_id(self, bicycle_id: str) -> None:
        self.__bicycle_id = bicycle_id
    
    def set_model(self, model: str) -> None:
        self.__model = model
    
    def set_type(self, bike_type: str) -> None:
        self.__type = bike_type
    
    def set_hourly_rate(self, hourly_rate: float) -> None:
        if hourly_rate < 0:
            raise InvalidBikeError("Цена за час не может быть отрицательной")
        self.__hourly_rate = hourly_rate
    
    def set_available(self, is_available: bool) -> None:
        self.__is_available = is_available
    
    @abstractmethod
    def calculate_rental_cost(self, hours: int) -> float:
        """Рассчитать стоимость аренды на основе часов"""
        pass
    
    def __str__(self) -> str:
        return f"Велосипед {self.__model}. Тип: {self.__type}"
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, Bicycle):
            return NotImplemented
        return self.__hourly_rate < other.__hourly_rate
    
    def __gt__(self, other) -> bool:
        if not isinstance(other, Bicycle):
            return NotImplemented
        return self.__hourly_rate > other.__hourly_rate
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Bicycle):
            return NotImplemented
        return self.__bicycle_id == other.__bicycle_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать велосипед в словарь для сериализации"""
        return {
            'bicycle_id': self.__bicycle_id,
            'model': self.__model,
            'type': self.__type,
            'hourly_rate': self.__hourly_rate,
            'is_available': self.__is_available
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Bicycle':
        """Создать велосипед из словаря"""
        bike_type = data.get('type', '').lower()
        if bike_type == 'city':
            return CityBike(
                data['bicycle_id'], data['model'], data['hourly_rate'],
                data.get('has_basket', False), data.get('is_available', True)
            )
        elif bike_type == 'mountain':
            return MountainBike(
                data['bicycle_id'], data['model'], data['hourly_rate'],
                data.get('suspension_type', 'Нет'), data.get('is_available', True)
            )
        elif bike_type == 'electric':
            return ElectricBike(
                data['bicycle_id'], data['model'], data['hourly_rate'],
                data.get('battery_life', 100), data.get('is_available', True)
            )
        else:
            raise InvalidBikeError(f"Неизвестный тип велосипеда: {bike_type}")

# ==================== Подклассы велосипедов ====================
class CityBike(Bicycle):
    """Городской велосипед с корзиной"""
    
    def __init__(self, bicycle_id: str, model: str, hourly_rate: float, has_basket: bool = False, is_available: bool = True):
        super().__init__(bicycle_id, model, "city", hourly_rate, is_available)
        self.__has_basket = has_basket
    
    def get_has_basket(self) -> bool:
        return self.__has_basket
    
    def set_has_basket(self, has_basket: bool) -> None:
        self.__has_basket = has_basket
    
    def calculate_rental_cost(self, hours: int) -> float:
        """Рассчитать стоимость со скидкой 10% для аренды более 5 часов"""
        base_cost = self.get_hourly_rate() * hours
        if hours > 5:
            base_cost *= 0.9
            self.log_action("расчет_стоимости", f"Применена скидка 10% за долгосрочную аренду")
        return base_cost
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['has_basket'] = self.__has_basket
        return data

class MountainBike(Bicycle):
    """Горный велосипед с амортизацией"""
    
    def __init__(self, bicycle_id: str, model: str, hourly_rate: float, suspension_type: str = "Нет", is_available: bool = True):
        super().__init__(bicycle_id, model, "mountain", hourly_rate, is_available)
        self.__suspension_type = suspension_type
    
    def get_suspension_type(self) -> str:
        return self.__suspension_type
    
    def set_suspension_type(self, suspension_type: str) -> None:
        self.__suspension_type = suspension_type
    
    def calculate_rental_cost(self, hours: int) -> float:
        """Стандартный расчет для горных велосипедов"""
        return self.get_hourly_rate() * hours
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['suspension_type'] = self.__suspension_type
        return data

class ElectricBike(Bicycle):
    """Электровелосипед с батареей"""
    
    def __init__(self, bicycle_id: str, model: str, hourly_rate: float, battery_life: int = 100, is_available: bool = True):
        super().__init__(bicycle_id, model, "electric", hourly_rate, is_available)
        self.__battery_life = battery_life
    
    def get_battery_life(self) -> int:
        return self.__battery_life
    
    def set_battery_life(self, battery_life: int) -> None:
        if 0 <= battery_life <= 100:
            self.__battery_life = battery_life
        else:
            raise InvalidBikeError("Заряд батареи должен быть от 0 до 100")
    
    def calculate_rental_cost(self, hours: int) -> float:
        """Рассчитать стоимость с учетом заряда батареи"""
        base_cost = self.get_hourly_rate() * hours
        if self.__battery_life < 20:
            base_cost *= 0.7
            self.log_action("расчет_стоимости", "Применена скидка 30% из-за низкого заряда батареи")
        return base_cost
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['battery_life'] = self.__battery_life
        return data

# ==================== Станция проката ====================
class RentalStation:
    """Станция проката велосипедов"""
    
    def __init__(self, station_id: str, location: str, capacity: int = 10):
        self.__station_id = station_id
        self.__location = location
        self.__capacity = capacity
        self.__bicycles: List[Bicycle] = []
    
    def get_station_id(self) -> str:
        return self.__station_id
    
    def get_location(self) -> str:
        return self.__location
    
    def add_bicycle(self, bicycle: Bicycle) -> bool:
        """Добавить велосипед на станцию"""
        if len(self.__bicycles) < self.__capacity:
            self.__bicycles.append(bicycle)
            logger.info(f"Велосипед {bicycle.get_bicycle_id()} добавлен на станцию {self.__station_id}")
            return True
        logger.warning(f"Не удалось добавить велосипед - станция {self.__station_id} заполнена")
        return False
    
    def remove_bicycle(self, bicycle_id: str) -> bool:
        """Удалить велосипед со станции"""
        for bike in self.__bicycles:
            if bike.get_bicycle_id() == bicycle_id:
                self.__bicycles.remove(bike)
                logger.info(f"Велосипед {bicycle_id} удален со станции {self.__station_id}")
                return True
        return False
    
    def get_available_bicycles(self) -> List[Bicycle]:
        """Получить список доступных велосипедов"""
        return [bike for bike in self.__bicycles if bike.is_available()]
    
    def get_all_bicycles(self) -> List[Bicycle]:
        """Получить все велосипеды на станции"""
        return self.__bicycles.copy()
    
    def search_by_model(self, model: str) -> List[Bicycle]:
        """Найти велосипеды по модели"""
        return [bike for bike in self.__bicycles if model.lower() in bike.get_model().lower()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать станцию в словарь для сериализации"""
        return {
            'station_id': self.__station_id,
            'location': self.__location,
            'capacity': self.__capacity,
            'bicycles': [bike.to_dict() for bike in self.__bicycles]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RentalStation':
        """Создать станцию из словаря"""
        station = cls(data['station_id'], data['location'], data['capacity'])
        for bike_data in data.get('bicycles', []):
            bike = Bicycle.from_dict(bike_data)
            station.add_bicycle(bike)
        return station

# ==================== Интерфейсы ====================
class Rentable(ABC):
    """Интерфейс для арендуемых предметов"""
    
    @abstractmethod
    def rent_bicycle(self, bicycle_id: str, hours: int) -> float:
        pass

class Reportable(ABC):
    """Интерфейс для генерации отчетов"""
    
    @abstractmethod
    def generate_report(self) -> str:
        pass

# ==================== Цепочка обязанностей ====================
class RentalRequest:
    """Запрос на изменение аренды"""
    
    def __init__(self, request_type: str, details: Dict[str, Any], cost_change: float = 0):
        self.request_type = request_type
        self.details = details
        self.cost_change = cost_change
        self.approved = False
        self.approved_by = None

class RequestHandler(ABC):
    """Абстрактный обработчик для цепочки обязанностей"""
    
    def __init__(self):
        self._next_handler = None
    
    def set_next(self, handler: 'RequestHandler') -> 'RequestHandler':
        self._next_handler = handler
        return handler
    
    @abstractmethod
    def handle(self, request: RentalRequest) -> bool:
        pass

class StationOperator(RequestHandler):
    """Оператор станции - может одобрить незначительные изменения"""
    
    def handle(self, request: RentalRequest) -> bool:
        if request.cost_change <= 5 and request.request_type in ['time_change', 'bike_swap']:
            request.approved = True
            request.approved_by = "Оператор станции"
            logger.info(f"Запрос одобрен оператором станции: {request.request_type}")
            return True
        elif self._next_handler:
            return self._next_handler.handle(request)
        return False

class Manager(RequestHandler):
    """Менеджер - может одобрить изменения с пересмотром стоимости"""
    
    def handle(self, request: RentalRequest) -> bool:
        if request.cost_change <= 20 and request.request_type in ['time_change', 'bike_swap', 'discount']:
            request.approved = True
            request.approved_by = "Менеджер"
            logger.info(f"Запрос одобрен менеджером: {request.request_type}")
            return True
        elif self._next_handler:
            return self._next_handler.handle(request)
        return False

class Admin(RequestHandler):
    """Администратор - может одобрить любое изменение"""
    
    def handle(self, request: RentalRequest) -> bool:
        request.approved = True
        request.approved_by = "Администратор"
        logger.info(f"Запрос одобрен администратором: {request.request_type}")
        return True

# ==================== Шаблонный метод ====================
class RentalProcess(ABC):
    """Шаблон для процесса аренды"""
    
    def rent_bicycle(self, station: RentalStation, bicycle_id: str, hours: int, user_id: str) -> Optional[Bicycle]:
        """Шаблонный метод, определяющий процесс аренды"""
        try:
            bicycle = self._check_availability(station, bicycle_id)
            if not bicycle:
                logger.warning(f"Велосипед {bicycle_id} недоступен")
                return None
            
            cost = self._process_rental(bicycle, hours)
            self._confirm_rental(bicycle, user_id, hours, cost)
            return bicycle
        except Exception as e:
            logger.error(f"Ошибка процесса аренды: {e}")
            return None
    
    def _check_availability(self, station: RentalStation, bicycle_id: str) -> Optional[Bicycle]:
        for bike in station.get_available_bicycles():
            if bike.get_bicycle_id() == bicycle_id:
                return bike
        return None
    
    @abstractmethod
    def _process_rental(self, bicycle: Bicycle, hours: int) -> float:
        pass
    
    @abstractmethod
    def _confirm_rental(self, bicycle: Bicycle, user_id: str, hours: int, cost: float) -> None:
        pass

class OnlineRentalProcess(RentalProcess):
    def _process_rental(self, bicycle: Bicycle, hours: int) -> float:
        cost = bicycle.calculate_rental_cost(hours)
        bicycle.log_action("оформление_аренды", f"Онлайн-обработка на {hours} часов")
        return cost
    
    def _confirm_rental(self, bicycle: Bicycle, user_id: str, hours: int, cost: float) -> None:
        bicycle.set_available(False)
        confirmation = f"Онлайн-аренда подтверждена: {bicycle.get_model()} на {hours} часов. Итого: {cost:.2f} руб."
        bicycle.log_action("подтверждение_аренды", confirmation)
        bicycle.send_notification(confirmation, "success")

class OfflineRentalProcess(RentalProcess):
    def _process_rental(self, bicycle: Bicycle, hours: int) -> float:
        cost = bicycle.calculate_rental_cost(hours)
        bicycle.log_action("оформление_аренды", f"Офлайн-обработка на {hours} часов")
        return cost
    
    def _confirm_rental(self, bicycle: Bicycle, user_id: str, hours: int, cost: float) -> None:
        bicycle.set_available(False)
        confirmation = f"Офлайн-аренда подтверждена: {bicycle.get_model()} на {hours} часов. Итого: {cost:.2f} руб."
        bicycle.log_action("подтверждение_аренды", confirmation)
        bicycle.send_notification(confirmation, "info")

# ==================== Декоратор для проверки прав ====================
def check_permissions(required_role: str):
    """Декоратор для проверки прав доступа пользователя"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, user_role: str, *args, **kwargs):
            roles_hierarchy = {
                'user': 0, 'пользователь': 0,
                'operator': 1, 'оператор': 1,
                'manager': 2, 'менеджер': 2,
                'admin': 3, 'администратор': 3
            }
            role_level = roles_hierarchy.get(user_role.lower(), 0)
            required_level = roles_hierarchy.get(required_role.lower(), 0)
            
            if role_level >= required_level:
                return func(self, user_role, *args, **kwargs)
            else:
                raise PermissionDeniedError(f"Недостаточно прав! Требуется роль: {required_role}")
        return wrapper
    return decorator

# ==================== Фабрика ====================
class BicycleFactory:
    """Фабрика для создания велосипедов"""
    
    @staticmethod
    def create_bicycle(bike_type: str, bicycle_id: str, model: str, hourly_rate: float, **kwargs) -> Bicycle:
        """Создать экземпляр велосипеда на основе типа"""
        bike_type_lower = bike_type.lower()
        
        if bike_type_lower in ['city', 'городской']:
            return CityBike(bicycle_id, model, hourly_rate, kwargs.get('has_basket', False))
        elif bike_type_lower in ['mountain', 'горный']:
            return MountainBike(bicycle_id, model, hourly_rate, kwargs.get('suspension_type', 'Нет'))
        elif bike_type_lower in ['electric', 'электро', 'электровелосипед']:
            return ElectricBike(bicycle_id, model, hourly_rate, kwargs.get('battery_life', 100))
        else:
            raise InvalidBikeError(f"Неизвестный тип велосипеда: {bike_type}")

# ==================== Основной сервис ====================
class RentalService(Rentable, Reportable):
    """Основной сервис для управления прокатом велосипедов"""
    
    def __init__(self):
        self.__stations: Dict[str, RentalStation] = {}
        self.__rentals: Dict[str, Dict[str, Any]] = {}
        self._chain = self._setup_chain()
        self._current_user_role = "user"  # роль по умолчанию
    
    def set_user_role(self, role: str) -> None:
        """Установить роль текущего пользователя"""
        self._current_user_role = role
    
    def _setup_chain(self) -> RequestHandler:
        operator = StationOperator()
        manager = Manager()
        admin = Admin()
        operator.set_next(manager).set_next(admin)
        return operator
    
    def add_station(self, station: RentalStation) -> None:
        self.__stations[station.get_station_id()] = station
        logger.info(f"Станция {station.get_station_id()} добавлена")
    
    def get_station(self, station_id: str) -> Optional[RentalStation]:
        return self.__stations.get(station_id)
    
    def rent_bicycle(self, station_id: str, bicycle_id: str, hours: int, user_id: str, process_type: str = "online") -> Optional[float]:
        """Арендовать велосипед"""
        station = self.get_station(station_id)
        if not station:
            logger.error(f"Станция {station_id} не найдена")
            return None
        
        process = OnlineRentalProcess() if process_type == "online" else OfflineRentalProcess()
        bicycle = process.rent_bicycle(station, bicycle_id, hours, user_id)
        
        if bicycle:
            cost = bicycle.calculate_rental_cost(hours)
            rental_id = f"{user_id}_{bicycle_id}_{datetime.now().timestamp()}"
            self.__rentals[rental_id] = {
                'bicycle_id': bicycle_id,
                'user_id': user_id,
                'hours': hours,
                'cost': cost,
                'timestamp': datetime.now().isoformat()
            }
            return cost
        return None
    
    def rent_bicycle_with_permission(self, user_role: str, station_id: str, bicycle_id: str, hours: int, user_id: str, process_type: str = "online") -> Optional[float]:
        """Арендовать велосипед с проверкой прав"""
        roles_hierarchy = {
            'user': 0, 'пользователь': 0,
            'operator': 1, 'оператор': 1,
            'manager': 2, 'менеджер': 2,
            'admin': 3, 'администратор': 3
        }
        if roles_hierarchy.get(user_role.lower(), 0) >= 1:
            return self.rent_bicycle(station_id, bicycle_id, hours, user_id, process_type)
        else:
            raise PermissionDeniedError(f"Недостаточно прав! Требуется роль: оператор")
    
    def modify_rental_request(self, request: RentalRequest) -> bool:
        return self._chain.handle(request)
    
    def generate_report(self) -> str:
        report = "=== ОТЧЕТ ПО АРЕНДЕ ВЕЛОСИПЕДОВ ===\n"
        report += f"Всего станций: {len(self.__stations)}\n"
        report += f"Всего аренд: {len(self.__rentals)}\n\n"
        
        report += "Детали станций:\n"
        for station in self.__stations.values():
            total_bikes = len(station.get_all_bicycles())
            available_bikes = len(station.get_available_bicycles())
            report += f"  - {station.get_station_id()}: {station.get_location()} (всего: {total_bikes}, доступно: {available_bikes})\n"
        
        report += "\nПоследние аренды:\n"
        for rental_id, rental in list(self.__rentals.items())[-5:]:
            report += f"  - {rental_id}: Велосипед {rental['bicycle_id']}, {rental['cost']:.2f} руб.\n"
        
        return report
    
    def save_to_file(self, filename: str) -> None:
        data = {
            'stations': [station.to_dict() for station in self.__stations.values()],
            'rentals': self.__rentals
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные сохранены в {filename}")
    
    def load_from_file(self, filename: str) -> None:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.__stations.clear()
        for station_data in data.get('stations', []):
            station = RentalStation.from_dict(station_data)
            self.__stations[station.get_station_id()] = station
        self.__rentals = data.get('rentals', {})
        logger.info(f"Данные загружены из {filename}")

# ==================== Пример использования ====================
if __name__ == "__main__":
    print("=" * 50)
    print("СЕРВИС ПРОКАТА ВЕЛОСИПЕДОВ")
    print("=" * 50)
    
    # 1. Создание велосипедов через фабрику
    print("\n1. Создание велосипедов:")
    bike1 = BicycleFactory.create_bicycle("city", "B001", "City Cruiser", 5.0, has_basket=True)
    bike2 = BicycleFactory.create_bicycle("mountain", "B002", "Trail Blazer", 7.0, suspension_type="Полная")
    bike3 = BicycleFactory.create_bicycle("electric", "B003", "E-Speed", 10.0, battery_life=75)
    
    print(f"  - {bike1}")
    print(f"  - {bike2}")
    print(f"  - {bike3}")
    
    # 2. Создание станции проката
    print("\n2. Создание станции проката:")
    station = RentalStation("S001", "Центральный парк", 10)
    station.add_bicycle(bike1)
    station.add_bicycle(bike2)
    station.add_bicycle(bike3)
    print(f"  Станция: {station.get_station_id()} - {station.get_location()}")
    print(f"  Доступно велосипедов: {len(station.get_available_bicycles())}")
    
    # 3. Создание сервиса
    print("\n3. Запуск сервиса проката:")
    service = RentalService()
    service.add_station(station)
    print("  Сервис готов к работе")
    
    # 4. Аренда велосипеда (с проверкой прав)
    print("\n4. Аренда велосипеда:")
    try:
        cost = service.rent_bicycle_with_permission("оператор", "S001", "B001", 3, "ПОЛЬЗОВАТЕЛЬ123", "online")
        if cost:
            print(f"  Успешно! Стоимость: {cost:.2f} руб.")
    except PermissionDeniedError as e:
        print(f"  Ошибка прав: {e}")
    
    # Пример с недостаточными правами
    print("\n  Проверка прав доступа (пользователь без прав):")
    try:
        cost = service.rent_bicycle_with_permission("пользователь", "S001", "B002", 2, "ПОЛЬЗОВАТЕЛЬ456", "online")
        print(f"  Стоимость: {cost:.2f} руб.")
    except PermissionDeniedError as e:
        print(f"  Ошибка (ожидаемо): {e}")
    
    # 5. Цепочка обязанностей
    print("\n5. Проверка согласования изменений:")
    req1 = RentalRequest("time_change", {"new_hours": 5}, 3)
    if service.modify_rental_request(req1):
        print(f"  Запрос на изменение времени одобрен: {req1.approved_by}")
    
    req2 = RentalRequest("discount", {"discount": 15}, 15)
    if service.modify_rental_request(req2):
        print(f"  Запрос на скидку одобрен: {req2.approved_by}")
    
    # 6. Отчет
    print("\n6. Генерация отчета:")
    print(service.generate_report())
    
    # 7. Уведомления
    print("\n7. Проверка уведомлений:")
    bike1.send_notification("Ваш велосипед City Cruiser готов к выдаче!", "success")
    bike1.log_action("начало_аренды", "Пользователь арендовал велосипед")
    
    # 8. Поиск велосипедов по модели
    print("\n8. Поиск велосипедов по модели 'Cruiser':")
    found = station.search_by_model("Cruiser")
    for bike in found:
        print(f"  Найден: {bike}")
    
    # 9. Сохранение данных
    print("\n9. Сохранение данных:")
    service.save_to_file("rental_data.json")
    print("  Данные сохранены в rental_data.json")
    
    # 10. Загрузка данных
    print("\n10. Загрузка данных в новый сервис:")
    new_service = RentalService()
    new_service.load_from_file("rental_data.json")
    print("  Данные успешно загружены")
    
    print("\n" + "=" * 50)
    print("ПРОГРАММА УСПЕШНО ЗАВЕРШЕНА")
    print("=" * 50)
