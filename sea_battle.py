from random import randint, random, choice

field_size = 8  # размер поля
ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]  # список с длинами кораблей для 8х8
# ships = [4, 3, 2, 1]  # список с длинами кораблей для 6х6


icons = {
    'sea': '~',
    'ship': '█',
    'hit': 'Ꭓ',
    'miss': '▪',
}



# ----------------------------------------------------------------------------------------------------------------------

class BoardException(Exception):
    """Общий класс, содержащий в себе все остальные классы исключений.
    Если мы хотим отловить несколько исключений, то их не нужно прописывать по отдельности"""
    pass


class BoardOutException(BoardException):
    """Если пользователь выстрелит за пределы доски, сработает это исключение.
     Пользовательский класс исключений"""

    def __str__(self):
        return "Выстрел за пределы поля!"


class BoardUsedException(BoardException):
    """Если пользователь выстрелит в уже задействованную клетку, сработает это исключение.
     Пользовательский класс исключений."""

    def __str__(self):
        return "Вы сюда уже стреляли!"


class BoardWrongShipException(BoardException):
    """Исключение для беспрепятственного размещения кораблей. Пользователю данное исключение не отображается."""
    pass


# ----------------------------------------------------------------------------------------------------------------------

class Cell:
    """Класс, содержащий все ячейки корабля на поле"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        """Сравнение ячеек"""
        return self.x == other.x and self.y == other.y

    def __sub__(self, other):
        """Разница ячеек"""
        return Cell(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        """Сумма ячеек"""
        return Cell(self.x + other.x, self.y + other.y)

    def __repr__(self):
        """Вывод представления ячейки в консоль"""
        return f"Cell({self.x}, {self.y})"


# ----------------------------------------------------------------------------------------------------------------------
class Shot:
    """Класс выстрела. Содержит координаты выстрела и его результат"""
    def __init__(self, d: Cell, result: str):
        self.coordinates = d
        self.result = result

    def get_result(self) -> str:
        return self.result

    def get_coords(self) -> Cell:
        return self.coordinates


# ----------------------------------------------------------------------------------------------------------------------
class Ship:
    """Класс Корабль"""

    def __init__(self, bow: Cell, ship_size: int, horizont: bool):
        self.bow = bow  # ячейка носа корабля
        self.length = ship_size  # длина корабля
        self.horizontal = horizont  # ориентация корабля (False - вертикальный, True - горизонтальный)
        self.lives = ship_size  # жизнь корабля измеряется его длинной

    @property
    def cells(self):
        ship_cells = []  # список с ячейками всего корабля
        for i in range(self.length):  # проходимся в цикле по значениям от 0 до (длинны корабля - 1)
            cur_x = self.bow.x  # текущая ячейка корабля
            cur_y = self.bow.y  # текущая ячейка корабля

            if self.horizontal:  # если горизонтальный
                cur_y += i  # ... то направление размещения по y
            else:
                cur_x += i  # ... иначе по х

            ship_cells.append(Cell(cur_x, cur_y))  # добавляем значение в список

        return ship_cells

    def hit(self, shot):
        """Проверка на попадание"""
        return shot in self.cells


# ----------------------------------------------------------------------------------------------------------------------

class Board:
    """Игровое поле"""

    def __init__(self, hide=False, size=6):
        self.hide = hide  # hide - нужно ли скрывать поле?
        self.size = size  # размер поля

        self.count = 0  # количество поражённых кораблей

        self.field = [[icons['sea']] * size for _ in range(size)]  # поле, в которой хранится состояние ячеек

        self.busy = []  # занятые ячейки (либо кораблём, либо выстрелом)
        self.ships = []  # список кораблей доски
        self.prev_hit = Shot(Cell(-1, -1), 'out')  # последнее успешное поражение корабля.
        self.first_hit = Shot(Cell(-1, -1), 'out')  # первое успешное поражение корабля в серии.

    def __str__(self):
        """Вывод корабля на доску"""
        res = " "
        for num in range(self.size):
            res += f" | {num + 1}"
        for i, row in enumerate(self.field):  # в цикле проходимся по строкам доски, берём индекс и...
            res += f"\n{i + 1} | " + " | ".join(row) + " |"  # ... выводим: номер строки | клетки строки

        if self.hide:
            res = res.replace(icons['ship'], icons['sea'])  # если True, заменяем все символы корабля на символы моря
        return res

    def get_num_field(self):

        def to_int(data):
            if data == icons['ship']:
                return 1
            else:
                return 0

        result = []
        for row in self.field:
            result.append(list(map(to_int, row)))
        return result

    def out(self, d):
        """Проверка на расположение ячейки за пределы поля"""
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def ship_board(self, ship, show=False):
        """Честный контур вокруг корабля"""
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]  # все направления ячеек вокруг текущей (сдвиги по диагонали и вертикали)
        for d in ship.cells:  # берём каждую ячейку корабля...
            for dx, dy in near:  # ...проходимся в цикле по списку направлений...
                cur = Cell(d.x + dx, d.y + dy)  # ...сдвигаем исходную ячейку на dx и dy
                if not (self.out(cur)) and cur not in self.busy:  # если она не выходит за пределы доски и не занята...
                    if show:  # если отображать
                        self.field[cur.x][cur.y] = icons['miss']  # ... то ставим знак промаха в ячейку
                    self.busy.append(cur)  # добавляем ячейку в список занятых

    def add_ship(self, ship):
        for d in ship.cells:  # проверка каждой ячейки корабля...
            if self.out(d) or d in self.busy:  # ... что она не выходит за границу и не занята.
                raise BoardWrongShipException()  # вызов исключения в случае проблемы
        for d in ship.cells:  # проверка каждой ячейки...
            self.field[d.x][d.y] = icons['ship']  # ... поставим в каждой ячейке палубу корабля
            self.busy.append(d)  # ... запишем ячейку в список занятых (ячейки расположения корабля или соседние)

        self.ships.append(ship)  # добавляем список собственных кораблей
        self.ship_board(ship)  # обводим список собственных кораблей по контуру

    def shot(self, d):
        """Выстрел"""
        if self.out(d):  # выходит ли ячейка за границу?...
            raise BoardOutException()  # ... если да, вызываем исключение

        if d in self.busy:  # занята ли ячейка?...
            raise BoardUsedException()  # ... если да, вызываем исключение

        self.busy.append(d)  # ячейка занята (если не была занята)

        for ship in self.ships:
            """Проходимся в цикле по кораблям и проверяем, принадлежит ли ячейка какому-либо кораблю или нет"""
            if ship.hit(d):  # если корабль был подстрелен...
                ship.lives -= 1  # уменьшаем количество жизней корабля
                self.field[d.x][d.y] = icons['hit']  # маркируем соответствующим образом ячейку
                if ship.lives == 0:  # если у корабля кончились жизни, то...
                    self.count += 1  # прибавляем к счётчику уничтоженных кораблей единицу
                    self.ship_board(ship, show=True)  # обводим корабль, чтобы контур обозначился ячейками
                    self.prev_hit = Shot(d, 'dead')
                    print("Корабль уничтожен")
                    return False
                else:
                    if self.prev_hit.result != 'hit':
                        self.first_hit = Shot(d, 'hit')
                    self.prev_hit = Shot(d, 'hit')
                    print("Корабль ранен!")
                    return True

        self.field[d.x][d.y] = icons['miss']  # если никакой корабль не поражён, срабатывает этот код
        print("Мимо!")
        return False

    def begin(self):
        self.busy = []  # обнуление списка использованных ячеек игры (тут будут сохраняться выстрелы игрока).

    def defeat(self):
        """Поражение"""
        return self.count == len(self.ships)

    def get_cell(self, d):
        """Выдаёт значение ячейки по координатам"""
        return self.field[d.x][d.y]

    def get_free_cross(self, d) -> list[Cell]:
        """Получение списка возможных ячеек для следующего выстрела по переданным координатам"""
        near = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        result = []
        for dx, dy in near:
            cur = Cell(d.x + dx, d.y + dy)
            if not self.out(cur) and cur in self.busy and self.get_cell(cur) == icons['hit']:
                cell = d + (d - cur)
                if not self.out(cell) and cell not in self.busy:
                    return [cell,]

            if not (self.out(cur)) and cur not in self.busy:
                result.append(cur)
        return result


# ----------------------------------------------------------------------------------------------------------------------
class Player:
    """Игрок"""

    def __init__(self, board: Board, enemy: Board):
        self.board = board  # поле игрока
        self.enemy = enemy  # поле противника

    def ask(self):
        raise NotImplementedError()  # при попытке вызвать метод будет вызываться исключение (метод должен быть у потомков класса)

    def move(self):
        """В бесконечном цикле пытаемся сделать выстрел"""
        while True:
            try:
                target = self.ask()  # просим компьютера или пользователя дать координаты выстрела
                repeat = self.enemy.shot(target)  # выполняем выстрел
                return repeat  # если выстрел успешен, возвращаем запрос на повторение хода
            except BoardException as e:  # если выстрел не удался, печатаем исключение
                print(e)


# ----------------------------------------------------------------------------------------------------------------------
class AI(Player):
    """Класс игрок-компьютер"""

    def ask(self):
        d = Cell(randint(0, field_size-1), randint(0, field_size-1))  # генерируем две случайные точки от 0 до размера карты
        if self.enemy.prev_hit.get_result() == 'hit':
            ds = self.enemy.get_free_cross(self.enemy.prev_hit.get_coords())
            if ds:
                d = choice(ds)
        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d

    def move(self):
        while True:
            try:
                target = self.ask()  # просим компьютера или пользователя дать координаты выстрела
                repeat = self.enemy.shot(target)  # выполняем выстрел
                if self.enemy.prev_hit.get_result() == 'hit' and not repeat:
                    self.enemy.prev_hit = self.enemy.first_hit
                return repeat  # если выстрел успешен, возвращаем запрос на повторение хода
            except BoardException as e:  # если выстрел не удался, печатаем исключение
                print(e)


class User(Player):
    def ask(self):
        while True:
            cords = input("Ваш ход: ").split()  # запрос координат

            if len(cords) != 2:  # проверка, что введены две координаты
                print("Введите 2 координаты! ")
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):  # проверяем, что введённое значение - число
                print(" Введите числа! ")
                continue

            x, y = int(x), int(y)

            return Cell(x - 1, y - 1)  # возвращаем нашу точку, не забыв вычесть единицу


"""Морской бой"""


def greet():
    print(f"""{'~' * 20}
Добро пожаловать
в игру
морской бой
{'~' * 20}
формат ввода: x y
x - номер строки
y - номер столбца""")


class Game:
    """Игра"""

    def __init__(self, ships_data, size=6):
        self.ships_data = ships_data
        self.size = size
        pl = self.random_board()  # генерируем случайную доску для игрока
        co = self.random_board()  # генерируем случайную доску для компьютера
        co.hide = True  # скрываем доску компьютера

        self.ai = AI(co, pl)  # создание игрока AI
        self.us = User(pl, co)  # создание игрока User

    def try_board(self):
        """Пытаемся создать доску и расставить на неё каждый корабль"""
        board = Board(size=self.size)  # создание доски
        attempts = 0  # количество попыток
        for ship_size in self.ships_data:  # для каждого размера корабля будем пытаться его поставить
            while True:
                attempts += 1
                if attempts > 888:
                    return None
                ship = Ship(Cell(randint(0, self.size), randint(0, self.size)), ship_size, random() >= 0.5)
                try:
                    board.add_ship(ship)  # попытка добавить корабль
                    break
                except BoardWrongShipException:
                    pass

        board.begin()
        return board

    def random_board(self):
        """Генерация случайной доски"""
        board = None  # пуская доска
        while board is None:  # создание доски в бесконечном цикле при условии, что доска пустая
            board = self.try_board()
        return board  # возвращаем непустую доску

    def loop(self):
        """Создаём игровой цикл"""
        num = 0  # номер хода
        while True:
            print(f"""{'~' * 20}
Доска пользователя: 
{self.us.board}
{'~' * 20}
Доска компьютера:
{self.ai.board}
{'~' * 20}""")
            if num % 2 == 0:  # если номер хода чётный, ходит пользователь
                print("Ходит пользователь!")
                repeat = self.us.move()  # записываем результат
            else:  # если номер хода нечётный, ходит компьютер
                print("Ходит компьютер!")
                repeat = self.ai.move()
            if repeat:  # ход остаётся у того же игрока, если попал
                num -= 1

            if self.ai.board.defeat():  # проверка на количество поражённых кораблей, равных количеству кораблей на доске
                print("~" * 20)
                print("Пользователь выиграл!")
                break

            if self.us.board.defeat():  # проверка на количество поражённых кораблей, равных количеству кораблей на доске
                print("~" * 20)
                print("Компьютер выиграл!")
                break
            num += 1

    def start(self):
        greet()
        self.loop()


g = Game(ships_data=ships, size=field_size)
g.start()
