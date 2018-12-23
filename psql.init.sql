CREATE OR REPLACE FUNCTION create_table(table_name TEXT, create_table_pattern text) RETURNS text AS
$$
    DECLARE
    create_cmd text;

    BEGIN
        IF EXISTS (
            SELECT *
            FROM   pg_catalog.pg_tables
            WHERE  tablename  = table_name
            ) THEN
           RETURN 'TABLE ' || table_name || ' ALREADY EXISTS';
        ELSE
           SELECT regexp_replace(create_table_pattern, '%tn%', table_name) into create_cmd;
           EXECUTE create_cmd;
           RETURN 'TABLE ' || table_name || ' CREATED';
        END IF;
    END;
$$ LANGUAGE plpgsql;



\set KK E'\'Краснодарский край\''
\set RO E'\'Ростовская область\''
\set SK E'\'Ставропольский край\''

CREATE TEMP TABLE temp_regions_and_cities (
    region_name,
    city_name
) AS VALUES
    (:KK, 'Краснодар'),
    (:KK, 'Кропоткин'),
    (:KK, 'Славянск'),
    ------------------------
    (:RO, 'Ростов-на-Дону'),
    (:RO, 'Шахты'),
    (:RO, 'Батайск'),
    ------------------------
    (:SK, 'Ставрополь'),
    (:SK, 'Пятигорск'),
    (:SK, 'Кисловодск');
    ------------------------
    -- insert new region here

SELECT create_table(
    'regions',

    'CREATE TABLE %tn% (
        region_id   serial primary key,
        region_name VARCHAR(50) unique not null
    );'
);

INSERT INTO regions (region_name)
    SELECT DISTINCT region_name
    FROM temp_regions_and_cities trc
    WHERE NOT EXISTS (
        SELECT 1
        FROM regions
        WHERE region_name = trc.region_name
    );

SELECT * from regions;

SELECT create_table(
    'cities',

    'CREATE TABLE %tn% (
        city_id   serial primary key,
        region_id INTEGER REFERENCES regions(region_id) ON DELETE CASCADE,
        city_name VARCHAR(30) unique not null
    );'
);

INSERT INTO cities (region_id, city_name)
    SELECT r.region_id, trc.city_name
    FROM regions r, temp_regions_and_cities trc
    WHERE r.region_name = trc.region_name AND NOT EXISTS (
        SELECT 1
        FROM cities
        WHERE city_name = trc.city_name
    );

SELECT * from cities;

SELECT create_table(
    'comments',

    'CREATE TABLE %tn% (
        comment_id   serial primary key,
        first_name   VARCHAR(30) not null,
        last_name    VARCHAR(30) not null,
        middle_name  VARCHAR(30) not null,
        email        VARCHAR(30) not null,
        phone        VARCHAR(16) not null,
        comment_text VARCHAR(255),
        city_id      INTEGER REFERENCES cities(city_id) ON DELETE CASCADE,
        created_at   TIMESTAMP DEFAULT NOW()
    );'
);
