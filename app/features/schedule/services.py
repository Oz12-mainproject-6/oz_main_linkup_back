def get_schedule_by_datetime(db: Session, artist: str, date: str, time: str):
    return db.query(models.Schedule).filter(
        models.Schedule.artist == artist,
        models.Schedule.date == date,
        models.Schedule.time == time
    ).first()