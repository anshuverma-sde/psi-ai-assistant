-- Runs once when the Postgres volume is first created.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE DATABASE psi_test OWNER psi;
\connect psi_test
CREATE EXTENSION IF NOT EXISTS vector;
