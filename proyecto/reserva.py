class Reservation:
    """Una reserva de una sala por un estudiante en un intervalo de tiempo."""
    def __init__(self, reservation_id, room_id, student_code, start, end, activity_detail,status="CONFIRMADA"):
        self.reservation_id = reservation_id
        self.room_id = room_id
        self.student_code = student_code
        self.start = start
        self.end = end
        self.status = status
        self.activity_detail = activity_detail