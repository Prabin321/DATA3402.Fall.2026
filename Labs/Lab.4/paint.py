import math

TOL = 1e-9


# Geometry helpers used for overlap checks.
def cross(a, b, p):
    return (
        (b[0] - a[0]) * (p[1] - a[1])
        - (b[1] - a[1]) * (p[0] - a[0])
    )


def on_segment(a, b, p):
    return (
        abs(cross(a, b, p)) <= TOL
        and min(a[0], b[0]) - TOL <= p[0] <= max(a[0], b[0]) + TOL
        and min(a[1], b[1]) - TOL <= p[1] <= max(a[1], b[1]) + TOL
    )


def edges_intersect(a, b, c, d):
    s1 = cross(a, b, c)
    s2 = cross(a, b, d)
    s3 = cross(c, d, a)
    s4 = cross(c, d, b)

    if s1 * s2 < 0 and s3 * s4 < 0:
        return True

    return (
        on_segment(a, b, c)
        or on_segment(a, b, d)
        or on_segment(c, d, a)
        or on_segment(c, d, b)
    )


def distance_to_segment(p, a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length_squared = dx * dx + dy * dy

    if length_squared == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])

    t = (
        (p[0] - a[0]) * dx + (p[1] - a[1]) * dy
    ) / length_squared

    t = max(0, min(1, t))

    closest_x = a[0] + t * dx
    closest_y = a[1] + t * dy

    return math.hypot(p[0] - closest_x, p[1] - closest_y)


class Canvas:
    # Adapted from the Canvas class in Lecture 9.
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [[' '] * width for i in range(height)]

    def set_pixel(self, row, col, char='*'):
        # Ignore pixels outside the canvas.
        if 0 <= row < self.height and 0 <= col < self.width:
            self.data[row][col] = char

    def get_pixel(self, row, col):
        return self.data[row][col]

    def clear_canvas(self):
        self.data = [
            [' '] * self.width for i in range(self.height)
        ]

    def v_line(self, x, y, w, **kwargs):
        for row in range(x, x + w):
            self.set_pixel(row, y, **kwargs)

    def h_line(self, x, y, h, **kwargs):
        for col in range(y, y + h):
            self.set_pixel(x, col, **kwargs)

    def line(self, x1, y1, x2, y2, **kwargs):
        # Arguments use the lecture's row/column convention.
        steps = math.ceil(max(abs(x2 - x1), abs(y2 - y1)))

        if steps == 0:
            self.set_pixel(round(x1), round(y1), **kwargs)
            return

        for i in range(steps + 1):
            fraction = i / steps
            row = round(x1 + fraction * (x2 - x1))
            col = round(y1 + fraction * (y2 - y1))
            self.set_pixel(row, col, **kwargs)

    def display(self):
        print("\n".join("".join(row) for row in self.data))


class Shape:
    def get_x(self):
        raise NotImplementedError

    def get_y(self):
        raise NotImplementedError

    def area(self):
        raise NotImplementedError

    def perimeter(self):
        raise NotImplementedError

    def perimeterPoints(self):
        raise NotImplementedError

    def contains(self, x, y):
        raise NotImplementedError

    def paint(self, canvas, char='*'):
        # Fill pixels that lie inside the shape.
        # Cartesian x becomes a column; y increases upward.
        for row in range(canvas.height):
            y = canvas.height - 1 - row

            for col in range(canvas.width):
                x = col

                if self.contains(x, y):
                    canvas.set_pixel(row, col, char)

    def overlaps(self, other):
        # Compound shapes overlap if any member overlaps.
        if isinstance(self, CompoundShape):
            return any(
                shape.overlaps(other) for shape in self.shapes
            )

        if isinstance(other, CompoundShape):
            return any(
                self.overlaps(shape) for shape in other.shapes
            )

        # Circle against circle.
        if isinstance(self, Circle) and isinstance(other, Circle):
            distance = math.hypot(
                self.get_x() - other.get_x(),
                self.get_y() - other.get_y()
            )

            return (
                distance
                <= self.get_radius() + other.get_radius() + TOL
            )

        # Circle against a rectangle or triangle.
        if isinstance(self, Circle) or isinstance(other, Circle):
            if isinstance(self, Circle):
                circle, polygon = self, other
            else:
                circle, polygon = other, self

            center = (circle.get_x(), circle.get_y())

            if polygon.contains(center[0], center[1]):
                return True

            points = polygon.perimeterPoints()

            for i in range(len(points)):
                a = points[i]
                b = points[(i + 1) % len(points)]

                if distance_to_segment(center, a, b) <= (
                    circle.get_radius() + TOL
                ):
                    return True

            return False

        # Rectangle/triangle against rectangle/triangle.
        points1 = self.perimeterPoints()
        points2 = other.perimeterPoints()

        for x, y in points1:
            if other.contains(x, y):
                return True

        for x, y in points2:
            if self.contains(x, y):
                return True

        for i in range(len(points1)):
            a = points1[i]
            b = points1[(i + 1) % len(points1)]

            for j in range(len(points2)):
                c = points2[j]
                d = points2[(j + 1) % len(points2)]

                if edges_intersect(a, b, c, d):
                    return True

        return False


class Rectangle(Shape):
    def __init__(self, length, width, x, y):
        if length <= 0 or width <= 0:
            raise ValueError("Dimensions must be positive.")

        self.__length = length
        self.__width = width
        self.__x = x
        self.__y = y

    def get_length(self):
        return self.__length

    def get_width(self):
        return self.__width

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def area(self):
        return self.__length * self.__width

    def perimeter(self):
        return 2 * (self.__length + self.__width)

    def perimeterPoints(self):
        x, y = self.__x, self.__y
        length, width = self.__length, self.__width

        return [
            (x, y),
            (x + length, y),
            (x + length, y + width),
            (x, y + width)
        ]

    def contains(self, x, y):
        return (
            self.__x <= x <= self.__x + self.__length
            and self.__y <= y <= self.__y + self.__width
        )


class Circle(Shape):
    def __init__(self, radius, x, y):
        if radius <= 0:
            raise ValueError("Radius must be positive.")

        self.__radius = radius
        self.__x = x
        self.__y = y

    def get_radius(self):
        return self.__radius

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def area(self):
        return math.pi * self.__radius ** 2

    def perimeter(self):
        return 2 * math.pi * self.__radius

    def perimeterPoints(self):
        points = []

        for i in range(16):
            angle = 2 * math.pi * i / 16

            x = self.__x + self.__radius * math.cos(angle)
            y = self.__y + self.__radius * math.sin(angle)

            points.append((x, y))

        return points

    def contains(self, x, y):
        distance = math.hypot(
            x - self.__x,
            y - self.__y
        )

        return distance <= self.__radius + TOL


class Triangle(Shape):
    def __init__(self, x1, y1, x2, y2, x3, y3):
        self.__x1 = x1
        self.__y1 = y1
        self.__x2 = x2
        self.__y2 = y2
        self.__x3 = x3
        self.__y3 = y3

        if self.area() == 0:
            raise ValueError("Vertices must not be collinear.")

    def get_x(self):
        return self.__x1

    def get_y(self):
        return self.__y1

    def get_x1(self):
        return self.__x1

    def get_y1(self):
        return self.__y1

    def get_x2(self):
        return self.__x2

    def get_y2(self):
        return self.__y2

    def get_x3(self):
        return self.__x3

    def get_y3(self):
        return self.__y3

    def area(self):
        return 0.5 * abs(
            self.__x1 * (self.__y2 - self.__y3)
            + self.__x2 * (self.__y3 - self.__y1)
            + self.__x3 * (self.__y1 - self.__y2)
        )

    def perimeter(self):
        d1 = math.hypot(
            self.__x2 - self.__x1,
            self.__y2 - self.__y1
        )

        d2 = math.hypot(
            self.__x3 - self.__x1,
            self.__y3 - self.__y1
        )

        d3 = math.hypot(
            self.__x3 - self.__x2,
            self.__y3 - self.__y2
        )

        return d1 + d2 + d3

    def perimeterPoints(self):
        return [
            (self.__x1, self.__y1),
            (self.__x2, self.__y2),
            (self.__x3, self.__y3)
        ]

    def contains(self, x, y):
        a, b, c = self.perimeterPoints()
        point = (x, y)

        s1 = cross(a, b, point)
        s2 = cross(b, c, point)
        s3 = cross(c, a, point)

        has_negative = s1 < -TOL or s2 < -TOL or s3 < -TOL
        has_positive = s1 > TOL or s2 > TOL or s3 > TOL

        return not (has_negative and has_positive)


class CompoundShape(Shape):
    def __init__(self, shapes):
        self.shapes = list(shapes)

    def contains(self, x, y):
        # A point belongs to the group if any member contains it.
        for shape in self.shapes:
            if shape.contains(x, y):
                return True

        return False

    def paint(self, canvas, char='*'):
        # Ask each member to paint itself on the same canvas.
        for shape in self.shapes:
            shape.paint(canvas, char)


class RasterDrawing:
    def __init__(self):
        self.shapes = {}

    def add_shape(self, name, shape):
        if name in self.shapes:
            raise ValueError("A shape with that name already exists.")

        self.shapes[name] = shape

    def get_shape(self, name):
        return self.shapes[name]

    def replace_shape(self, name, new_shape):
        if name not in self.shapes:
            raise KeyError("No shape exists with that name.")

        self.shapes[name] = new_shape

    def remove_shape(self, name):
        del self.shapes[name]

    def paint(self, canvas):
        for shape in self.shapes.values():
            shape.paint(canvas)

    def update(self, canvas):
        # Remove the previous image before drawing the current shapes.
        canvas.clear_canvas()
        self.paint(canvas)
