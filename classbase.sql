CREATE TABLE classroom (
  building      VARCHAR (15),
  room_number   VARCHAR (7),
  ip            VARCHAR (15),
  PRIMARY KEY (ip)
);

CREATE TABLE deparment (
  dept_name   VARCHAR (20),
  building    VARCHAR (15),
  PRIMARY KEY (dept_name)
);

CREATE TABLE course (
  course_id     VARCHAR (8),
  title         VARCHAR (50),
  dept_name     VARCHAR (20),
  PRIMARY KEY (course_id),
  FOREIGN KEY (dept_name) REFERENCES deparment
  ON DELETE SET NULL
);

CREATE TABLE instructor (
  id          VARCHAR (10),
  name        VARCHAR (20) NOT NULL,
  dept_name   VARCHAR (20),
  PRIMARY KEY (id),
  FOREIGN KEY (dept_name) REFERENCES deparment
  ON DELETE SET NULL
);

CREATE TABLE clerk (
  id          VARCHAR (10),
  name        VARCHAR (20) NOT NULL,
  FOREIGN KEY (id) REFERENCES instructor
  ON DELETE CASCADE
);

CREATE TABLE section (
  course_id     VARCHAR (8),
  sec_id        VARCHAR (8),
  semester      VARCHAR (6) CHECK (semester in ('Spring', 'Fall')),
  year          NUMERIC (4, 0) CHECK (year > 1900 AND year < 2100),
  ip            VARCHAR (15),
  time_slot_id  VARCHAR (4),
  PRIMARY KEY (course_id, sec_id),
  FOREIGN KEY (course_id) REFERENCES course
  ON DELETE CASCADE,
  FOREIGN KEY (ip) REFERENCES classroom
  ON DELETE SET NULL
);

CREATE TABLE id_password (
  id          VARCHAR (10),
  password    VARCHAR (12) NOT NULL,
  FOREIGN KEY (id) REFERENCES instructor
  ON DELETE CASCADE
);

CREATE TABLE course_instructor (
  id            VARCHAR (10),
  course_id     VARCHAR (8),
  sec_id        VARCHAR (8),
  FOREIGN KEY (id) REFERENCES instructor
  ON DELETE SET NULL,
  FOREIGN KEY (course_id, sec_id) REFERENCES section
  ON DELETE CASCADE
);

CREATE TABLE time_slot (
  time_slot_id    VARCHAR (4),
  day             VARCHAR (1) CHECK (day in ('M', 'T', 'W', 'R', 'F', 'S', 'U')),
  start_time      TIME,
  end_time        TIME,
  PRIMARY KEY (time_slot_id, day, start_time)
);
