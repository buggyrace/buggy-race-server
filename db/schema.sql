------ ===========================================================================
------ This file is a manual PostgreSQL database schema dump
------
------ ...so you if you can't run the Flask/alembic migrations you can still
------ manually create the database. (You may have problems later on — if there
------ are new migrations released after you've installed — if you do this!)
------
------ Snapshot of migrations directory when this schema.sql was created:
------      00152d1270ad_record_user_s_first_login.py
------      1c327d0803e4_explicit_user_enable_login.py
------      8541b7aad85a_v2_0_2_with_timestamps.py
------
------ Devs! Please keep this up-to-date after migrations (e.g., from heroku):
------
------      pg_dump --schema-only --no-owner DATABASE_URL > schema.sql
------
------ (for heroku CLI, do "heroku run -a heroku-app-name 'command' > schema.sql")
------
------  * DATABASE_URL may be like postgres://username:pw@host:port/name
------  * --schema-only for stucture not data
------  * --no-owner to avoid Heroku usernames etc (this isn't for restore!)
------
------ ...then add a helpful comment like this and drop it in as schema.sql :-)
------ ===========================================================================

-
-- PostgreSQL database dump
--

-- Dumped from database version 15.1
-- Dumped by pg_dump version 15.1

-- Started on 2024-06-20 13:05:50 BST

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

SET default_table_access_method = heap;

--
-- TOC entry 214 (class 1259 OID 45429)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- TOC entry 215 (class 1259 OID 45432)
-- Name: announcements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.announcements (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    text text NOT NULL,
    type character varying(32),
    is_visible boolean,
    is_html boolean
);


--
-- TOC entry 216 (class 1259 OID 45437)
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
-- TOC entry 3693 (class 0 OID 0)
-- Dependencies: 216
-- Name: announcements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.announcements_id_seq OWNED BY public.announcements.id;


--
-- TOC entry 217 (class 1259 OID 45438)
-- Name: buggies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.buggies (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
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
-- TOC entry 218 (class 1259 OID 45441)
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
-- TOC entry 3694 (class 0 OID 0)
-- Dependencies: 218
-- Name: buggies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.buggies_id_seq OWNED BY public.buggies.id;


--
-- TOC entry 219 (class 1259 OID 45442)
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
-- TOC entry 220 (class 1259 OID 45447)
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
-- TOC entry 3695 (class 0 OID 0)
-- Dependencies: 220
-- Name: db_files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.db_files_id_seq OWNED BY public.db_files.id;


--
-- TOC entry 221 (class 1259 OID 45448)
-- Name: races; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.races (
    id integer NOT NULL,
    title character varying(80) NOT NULL,
    "desc" text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    start_at timestamp with time zone NOT NULL,
    cost_limit integer,
    is_visible boolean,
    race_file_url character varying(255),
    league character varying(32),
    results_uploaded_at timestamp with time zone,
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
-- TOC entry 222 (class 1259 OID 45453)
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
-- TOC entry 3696 (class 0 OID 0)
-- Dependencies: 222
-- Name: races_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.races_id_seq OWNED BY public.races.id;


--
-- TOC entry 223 (class 1259 OID 45454)
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
-- TOC entry 224 (class 1259 OID 45459)
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
-- TOC entry 3697 (class 0 OID 0)
-- Dependencies: 224
-- Name: racetracks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.racetracks_id_seq OWNED BY public.racetracks.id;


--
-- TOC entry 225 (class 1259 OID 45460)
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
-- TOC entry 226 (class 1259 OID 45463)
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
-- TOC entry 3698 (class 0 OID 0)
-- Dependencies: 226
-- Name: results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.results_id_seq OWNED BY public.results.id;


--
-- TOC entry 227 (class 1259 OID 45464)
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    name character varying(80) NOT NULL,
    user_id integer,
    id integer NOT NULL
);


--
-- TOC entry 228 (class 1259 OID 45467)
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
-- TOC entry 3699 (class 0 OID 0)
-- Dependencies: 228
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- TOC entry 229 (class 1259 OID 45468)
-- Name: settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.settings (
    id character varying(64) NOT NULL,
    value character varying(255) NOT NULL
);


--
-- TOC entry 230 (class 1259 OID 45471)
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    modified_at timestamp with time zone,
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
-- TOC entry 231 (class 1259 OID 45476)
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
-- TOC entry 3700 (class 0 OID 0)
-- Dependencies: 231
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- TOC entry 232 (class 1259 OID 45477)
-- Name: tasktexts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasktexts (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    modified_at timestamp with time zone,
    user_id integer NOT NULL,
    task_id integer NOT NULL,
    text text NOT NULL
);


--
-- TOC entry 233 (class 1259 OID 45482)
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
-- TOC entry 3701 (class 0 OID 0)
-- Dependencies: 233
-- Name: tasktexts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tasktexts_id_seq OWNED BY public.tasktexts.id;


--
-- TOC entry 234 (class 1259 OID 45483)
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    username character varying(80) NOT NULL,
    ext_username character varying(80),
    ext_id character varying(80),
    email character varying(80),
    password bytea,
    created_at timestamp with time zone,
    first_name character varying(30),
    last_name character varying(30),
    is_active boolean,
    is_admin boolean,
    access_level integer NOT NULL,
    latest_json text,
    github_username text,
    github_access_token text,
    is_student boolean,
    logged_in_at timestamp with time zone,
    uploaded_at timestamp with time zone,
    api_secret character varying(30),
    api_secret_at timestamp with time zone,
    api_secret_count integer NOT NULL,
    is_api_secret_otp boolean NOT NULL,
    api_key character varying(30),
    comment text,
    is_demo_user boolean,
    id integer NOT NULL,
    first_logged_in_at timestamp with time zone,
    is_login_enabled boolean DEFAULT true NOT NULL
);


--
-- TOC entry 235 (class 1259 OID 45488)
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
-- TOC entry 3702 (class 0 OID 0)
-- Dependencies: 235
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 3492 (class 2604 OID 45489)
-- Name: announcements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.announcements ALTER COLUMN id SET DEFAULT nextval('public.announcements_id_seq'::regclass);


--
-- TOC entry 3493 (class 2604 OID 45490)
-- Name: buggies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.buggies ALTER COLUMN id SET DEFAULT nextval('public.buggies_id_seq'::regclass);


--
-- TOC entry 3494 (class 2604 OID 45491)
-- Name: db_files id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.db_files ALTER COLUMN id SET DEFAULT nextval('public.db_files_id_seq'::regclass);


--
-- TOC entry 3495 (class 2604 OID 45492)
-- Name: races id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.races ALTER COLUMN id SET DEFAULT nextval('public.races_id_seq'::regclass);


--
-- TOC entry 3496 (class 2604 OID 45493)
-- Name: racetracks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.racetracks ALTER COLUMN id SET DEFAULT nextval('public.racetracks_id_seq'::regclass);


--
-- TOC entry 3497 (class 2604 OID 45494)
-- Name: results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results ALTER COLUMN id SET DEFAULT nextval('public.results_id_seq'::regclass);


--
-- TOC entry 3498 (class 2604 OID 45495)
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- TOC entry 3499 (class 2604 OID 45496)
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- TOC entry 3500 (class 2604 OID 45497)
-- Name: tasktexts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts ALTER COLUMN id SET DEFAULT nextval('public.tasktexts_id_seq'::regclass);


--
-- TOC entry 3501 (class 2604 OID 45498)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3504 (class 2606 OID 45517)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3506 (class 2606 OID 45519)
-- Name: announcements announcements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.announcements
    ADD CONSTRAINT announcements_pkey PRIMARY KEY (id);


--
-- TOC entry 3508 (class 2606 OID 45521)
-- Name: buggies buggies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.buggies
    ADD CONSTRAINT buggies_pkey PRIMARY KEY (id);


--
-- TOC entry 3510 (class 2606 OID 45523)
-- Name: db_files db_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.db_files
    ADD CONSTRAINT db_files_pkey PRIMARY KEY (id);


--
-- TOC entry 3512 (class 2606 OID 45525)
-- Name: races races_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.races
    ADD CONSTRAINT races_pkey PRIMARY KEY (id);


--
-- TOC entry 3514 (class 2606 OID 45527)
-- Name: races races_race_file_url_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.races
    ADD CONSTRAINT races_race_file_url_key UNIQUE (race_file_url);


--
-- TOC entry 3516 (class 2606 OID 45529)
-- Name: racetracks racetracks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.racetracks
    ADD CONSTRAINT racetracks_pkey PRIMARY KEY (id);


--
-- TOC entry 3518 (class 2606 OID 45531)
-- Name: results results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_pkey PRIMARY KEY (id);


--
-- TOC entry 3520 (class 2606 OID 45533)
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- TOC entry 3522 (class 2606 OID 45535)
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3524 (class 2606 OID 45537)
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3526 (class 2606 OID 45539)
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- TOC entry 3528 (class 2606 OID 45541)
-- Name: tasktexts tasktexts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts
    ADD CONSTRAINT tasktexts_pkey PRIMARY KEY (id);


--
-- TOC entry 3530 (class 2606 OID 45543)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 3532 (class 2606 OID 45545)
-- Name: users users_ext_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_ext_id_key UNIQUE (ext_id);


--
-- TOC entry 3534 (class 2606 OID 45547)
-- Name: users users_ext_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_ext_username_key UNIQUE (ext_username);


--
-- TOC entry 3536 (class 2606 OID 45549)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3538 (class 2606 OID 45551)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 3539 (class 2606 OID 45552)
-- Name: buggies buggies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.buggies
    ADD CONSTRAINT buggies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3540 (class 2606 OID 45557)
-- Name: db_files db_files_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.db_files
    ADD CONSTRAINT db_files_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.races(id);


--
-- TOC entry 3541 (class 2606 OID 45562)
-- Name: results results_race_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_race_id_fkey FOREIGN KEY (race_id) REFERENCES public.races(id);


--
-- TOC entry 3542 (class 2606 OID 45567)
-- Name: results results_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3543 (class 2606 OID 45572)
-- Name: roles roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3544 (class 2606 OID 45577)
-- Name: tasktexts tasktexts_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts
    ADD CONSTRAINT tasktexts_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- TOC entry 3545 (class 2606 OID 45582)
-- Name: tasktexts tasktexts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasktexts
    ADD CONSTRAINT tasktexts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


-- Completed on 2024-06-20 13:05:50 BST

--
-- PostgreSQL database dump complete
--

