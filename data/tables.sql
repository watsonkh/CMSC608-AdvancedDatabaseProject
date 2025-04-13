-- CREATE EXTENSION will print an unnecessary message if the extension is already installed
-- so we suppress it by setting client_min_messages to WARNING
SET client_min_messages TO WARNING;
CREATE EXTENSION IF NOT EXISTS vector;
RESET client_min_messages;

-- Creates an enumeration type for unit types if it doesn't already exist
-- This fails if it exists, so we check for existence first
-- The IF NOT EXISTS requires a DO block in plsql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'unit_type') THEN
        CREATE TYPE unit_type AS ENUM ('volume', 'mass', 'count', 'length', 'area', 'use');
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS unit (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  unitType unit_type NOT NULL,
  notation TEXT NOT NULL,
  UNIQUE (name));

CREATE TABLE IF NOT EXISTS unit_conversion (
  id SERIAL PRIMARY KEY,
  fromUnit BIGINT NOT NULL,
  toUnit BIGINT NOT NULL,
  ratio NUMERIC NOT NULL,
  UNIQUE (fromUnit, toUnit),
  FOREIGN KEY (fromUnit) REFERENCES unit(id),
  FOREIGN KEY (toUnit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS ingredient (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  baseUnit BIGINT NOT NULL,
  externalLink TEXT,
  UNIQUE (name),
  FOREIGN KEY (baseUnit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS ingredient_unit_conversion (
  id SERIAL PRIMARY KEY,
  ingredient BIGINT NOT NULL,
  fromUnit BIGINT NOT NULL,
  toUnit BIGINT NOT NULL,
  ratio NUMERIC NOT NULL,
  UNIQUE (ingredient, fromUnit, toUnit),
  FOREIGN KEY (ingredient) REFERENCES ingredient(id),
  FOREIGN KEY (fromUnit) REFERENCES unit(id),
  FOREIGN KEY (toUnit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS substitution (
  id SERIAL PRIMARY KEY,
  firstIngredient BIGINT NOT NULL,
  secondIngredient BIGINT NOT NULL,
  note text NOT NULL,
  UNIQUE (firstIngredient, secondIngredient),
  FOREIGN KEY (firstIngredient) REFERENCES ingredient(id),
  FOREIGN KEY (secondIngredient) REFERENCES ingredient(id));

CREATE TABLE IF NOT EXISTS recipe (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  servings VARCHAR NOT NULL,
  mainImage TEXT,
  source TEXT,
  UNIQUE (name));

CREATE TABLE IF NOT EXISTS recipe_ingredient (
  id SERIAL PRIMARY KEY,
  recipeId BIGINT NOT NULL,
  ingredientId BIGINT NOT NULL,
  displayOrder INT NOT NULL,
  unit BIGINT NOT NULL,
  quantity NUMERIC NOT NULL,
  denominator INT,
  UNIQUE (recipeId, ingredientId, displayOrder),
  FOREIGN KEY (recipeId) REFERENCES recipe(id),
  FOREIGN KEY (ingredientId) REFERENCES ingredient(id),
  FOREIGN KEY (unit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS step (
  id SERIAL PRIMARY KEY,
  recipeId BIGINT NOT NULL,
  displayOrder INT NOT NULL,
  description TEXT NOT NULL,
  imageLocation TEXT,
  UNIQUE (recipeId, displayOrder),
  FOREIGN KEY (recipeId) REFERENCES recipe(id));

CREATE TABLE IF NOT EXISTS image (
  id SERIAL PRIMARY KEY,
  recipeId BIGINT NOT NULL,
  imageLocation TEXT NOT NULL,
  embedding vector(512) NOT NULL,
  UNIQUE (recipeId, imageLocation),
  FOREIGN KEY (recipeId) REFERENCES recipe(id));

CREATE INDEX IF NOT EXISTS hnsw_embedding_idx ON image
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);


CREATE TABLE IF NOT EXISTS recipe_embeddings(
  recipeId BIGINT NOT NULL PRIMARY KEY,
  description_embedding vector(768) NOT NULL,
  FOREIGN KEY (recipeId) REFERENCES recipe(id));

CREATE INDEX ON recipe_embeddings USING ivfflat (description_embedding vector_ip_ops) WITH (lists = 10);

