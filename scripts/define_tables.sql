-- DO NOT RUN THIS FILE AS-IS. BE SURE TO READ AND UNDERSTAND IT BEFORE CREATING A NEW MYSQL DATABASE

CREATE TABLE IF NOT EXISTS sources (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    url_prefix    VARCHAR(255) NOT NULL
) ENGINE=INNODB;

-- POPULATE THE sources TABLE WITH YOUR IMAGE SERVER(S)
INSERT INTO `sources` (`name`,`url_prefix`) VALUES ('RockMaker1','http://rockmaker_image_server_1:9001');
INSERT INTO `sources` (`name`,`url_prefix`) VALUES ('RockMaker2','http://rockmaker_image_server_2:9002');

CREATE TABLE IF NOT EXISTS image_scores (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    source_id      INT NOT NULL,
    date_scored    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scored_by      VARCHAR(255) NOT NULL,
    plate_num      INT NOT NULL,
    plate_id       INT NOT NULL,
    barcode        VARCHAR(255) NOT NULL,
    relative_path  VARCHAR(255) NOT NULL,
    well_num       INT NOT NULL,
    row_letter     VARCHAR(2) NOT NULL,
    column_num     INT NOT NULL,
    drop_num       INT NOT NULL,
    date_imaged    DATETIME NOT NULL,
    classification TEXT NOT NULL,
    crystal        FLOAT,
    clear          FLOAT,
    other          FLOAT,
    precipitate    FLOAT,
    date_dispensed DATETIME,
    temperature    FLOAT
) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS disputes (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    image_score_id INT NOT NULL,
    disputed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    disputed_by    VARCHAR(255),
    manual_call    VARCHAR(255)
) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS favorites (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    image_score_id INT NOT NULL,
    favorited_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    favorited_by   VARCHAR(255),
    plate_id       INT NOT NULL,
    well_num       INT NOT NULL,
    drop_num       INT NOT NULL
) ENGINE=INNODB;
