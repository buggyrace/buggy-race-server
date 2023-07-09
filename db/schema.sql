----- ===========================================================================
----- This file is a manual PostgreSQL database schema dump
-----
----- ...so you if you can't run the Flask/alembic migrations you can still
----- manually create the database. (You may have problems later on — if there
----- are new migrations released after you've installed — if you do this!)
-----
----- Snapshot of migrations directory when this was schema.sql was created:
-----      cb8d854af019_v2_0_1_with_db_files.py
-----
----- Devs! Please keep this up-to-date after migrations (e.g., from heroku):
-----
-----      pg_dump --schema-only --no-owner DATABASE_URL > schema.sql
-----
----- (for heroku CLI, do "heroku run -a heroku-app-name 'command' > schema.sql")
-----
-----  * DATABASE_URL may be like postgres://username:pw@host:port/name
-----  * --schema-only for stucture not data
-----  * --no-owner to avoid Heroku usernames etc (this isn't for restore!)
-----
----- ...then add a helpful comment like this and drop it in as schema.sql :-)
----- ===========================================================================

--
-- PostgreSQL database dump
--

-- Dumped from database version 15.1
-- Dumped by pg_dump version 15.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: announcements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.announcements (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    text text NOT NULL,
    type character varying(32),
    is_visible boolean,
    is_html boolean
);


--
-- Name: announcements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.announcements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: announcements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.announcements_id_seq OWNED BY public.announcements.id;


--
-- Name: buggies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.buggies (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    buggy_id integer,
    qty_wheels integer,
    flag_color character varying(32),
    flag_color_secondary character varying(32),
    flag_pattern character varying(8),
    power_type character varying(16),
    power_units integer,
    aux_power_type character varying(16),
    aux_power_units integer,
    tyres character varying(16),
    qty_tyres integer,
    armour character varying(16),
    attack character varying(16),
    qty_attacks integer,
    hamster_booster integer,
    fireproof boolean,
    insulated boolean,
    antibiotic boolean,
    banging boolean,
    algo character varying(16),
    user_id integer NOT NULL,
    total_cost integer,
    mass integer
);


--
-- Name: buggies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.buggies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: buggies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.buggies_id_seq OWNED BY public.buggies.id;


--
-- Name: db_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.db_files (
    id integer NOT NULL,
    type character varying(8) NOT NULL,
    name character varying(64),
    item_id integer,
    contents text NOT NULL
);


--
-- Name: db_files_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.db_files_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: db_files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.db_files_id_seq OWNED BY public.db_files.id;


--
-- Name: races; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.races (
    id integer NOT NULL,
    title character varying(80) NOT NULL,
    "desc" text NOT NULL,
    created_at timestamp without time zone NOT NULL,
    start_at timestamp without time zone NOT NULL,
    cost_limit integer,
    is_visible boolean,
    race_file_url character varying(255),
    league character varying(32),
    results_uploaded_at timestamp without time zone,
    buggies_entered integer NOT NULL,
    buggies_started integer NOT NULL,
    buggies_finished integer NOT NULL,
    is_result_visible boolean NOT NULL,
    track_image_url character varying(255),
    track_svg_url character varying(255),
    max_laps integer,
    lap_length integer,
    is_dnf_position boolean NOT NULL,
    is_abandoned boolean NOT NULL
);


--
-- Name: races_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.races_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: races_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.races_id_seq OWNED BY public.races.id;


--
-- Name: racetracks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.racetracks (
    id integer NOT NULL,
    title character varying(80) NOT NULL,
    "desc" text NOT NULL,
    track_image_url character varying(255),
    track_svg_url character varying(255),
    lap_length integer
);


--
-- Name: racetracks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.racetracks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: racetracks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.racetracks_id_seq OWNED BY public.racetracks.id;


--
-- Name: results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.results (
    id integer NOT NULL,
    race_id integer NOT NULL,
    user_id integer NOT NULL,
    flag_color character varying(32) NOT NULL,
    flag_color_secondary character varying(32) NOT NULL,
    flag_pattern character varying(32) NOT NULL,
    cost integer,
    race_position integer NOT NULL,
    violations_str character varying(255)
);


--
-- Name: results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.results_id_seq OWNED BY public.results.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    name character varying(80) NOT NULL,
    user_id integer,
    id integer NOT NULL
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.settings (
    id character varying(64) NOT NULL,
    value character varying(255) NOT NULL
);


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    modified_at timestamp without time zone,
    phase integer NOT NULL,
    name character varying(16) NOT NULL,
    title character varying(80) NOT NULL,
    problem_text text NOT NULL,
    solution_text text NOT NULL,
    hints_text text NOT NULL,
    is_enabled boolean NOT NULL,
    sort_position integer NOT NULL
);


--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: tasktexts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasktexts (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    modified_at timestamp without time zone,
    user_id integer NOT NULL,
    task_id integer NOT NULL,
    text text NOT NULL
);


--
-- Name: tasktexts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tasktexts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tasktexts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tasktexts_id_seq OWNED BY public.tasktexts.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    username character varying(80) NOT NULL,
    ext_username character varying(80),
    ext_id character varying(80),
    email character varying(80),
    password bytea,
    created_at timestamp without time zone NOT NULL,
    first_name character varying(30),
    last_name character varying(30),
    is_active boolean,
    is_admin boolean,
    access_level integer NOT NULL,
    latest_json text,
    github_username text,
    github_access_token text,
    is_student boolean,
    logged_in_at timestamp without time zone,
    uploaded_at timestamp without time zone,
    api_secret character varying(30),
    api_secret_at timestamp without time zone,
    api_secret_count integer NOT NULL,
    is_api_secret_otp boolean NOT NULL,
    api_key character varying(30),
    comment text,
    is_demo_user boolean,
    id integer NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: announcements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.announcements ALTER COLUMN id SET DEFAULT nextval('public.announcements_id_seq'::regclass);


--
-- Name: buggies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.buggies ALTER COLUMN id SET DEFAULT nextval('public.buggies_id_seq'::regclass);


--
-- Name: db_files id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.db_files ALTER COLUMN id SET DEFAULT nextval('public.db_files_id_seq'::regclass);


--
-- Name: races id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.races ALTER COLUMN id SET DEFAULT nextval('public.races_id_seq'::regclass);


--
-- Name: racetracks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.racetracks ALTER COLUMN id SET DEFAULT nextval('public.racetracks_id_seq'::regclass);


--
-- Name: results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results ALTER COLUMN id SET DEFAULT nextval('public.results_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: tasktexts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts ALTER COLUMN id SET DEFAULT nextval('public.tasktexts_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: announcements announcements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.announcements
    ADD CONSTRAINT announcements_pkey PRIMARY KEY (id);


--
-- Name: buggies buggies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.buggies
    ADD CONSTRAINT buggies_pkey PRIMARY KEY (id);


--
-- Name: db_files db_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.db_files
    ADD CONSTRAINT db_files_pkey PRIMARY KEY (id);


--
-- Name: races races_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.races
    ADD CONSTRAINT races_pkey PRIMARY KEY (id);


--
-- Name: races races_race_file_url_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.races
    ADD CONSTRAINT races_race_file_url_key UNIQUE (race_file_url);


--
-- Name: racetracks racetracks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.racetracks
    ADD CONSTRAINT racetracks_pkey PRIMARY KEY (id);


--
-- Name: results results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: tasktexts tasktexts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts
    ADD CONSTRAINT tasktexts_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_ext_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_ext_id_key UNIQUE (ext_id);


--
-- Name: users users_ext_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_ext_username_key UNIQUE (ext_username);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: buggies buggies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.buggies
    ADD CONSTRAINT buggies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: db_files db_files_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.db_files
    ADD CONSTRAINT db_files_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.races(id);


--
-- Name: results results_race_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_race_id_fkey FOREIGN KEY (race_id) REFERENCES public.races(id);


--
-- Name: results results_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: roles roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: tasktexts tasktexts_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts
    ADD CONSTRAINT tasktexts_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: tasktexts tasktexts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts
    ADD CONSTRAINT tasktexts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

