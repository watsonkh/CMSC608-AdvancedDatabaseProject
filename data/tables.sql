CREATE TABLE IF NOT EXISTS unit (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  unitType ENUM('volume', 'mass', 'count', 'length', 'area') NOT NULLi,
  notation TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS unit_conversion (
  id SERIAL PRIMARY KEY,
  fromUnit BIGINT NOT NULL,
  toUnit BIGINT NOT NULL,
  ratio NUMERIC NOT NULL
  FOREIGN KEY (fromUnit) REFERENCES unit(id),
  FOREIGN KEY (toUnit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS ingredient (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  baseUnit BIGINT NOT NULL,
  externalLink TEXT,
  FOREIGN KEY (baseUnit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS ingredient_unit_conversion (
  id SERIAL PRIMARY KEY,
  ingredient BIGINT NOT NULL,
  fromUnit BIGINT NOT NULL,
  toUnit BIGINT NOT NULL,
  ratio NUMERIC NOT NULL,
  FOREIGN KEY (ingredient) REFERENCES ingredient(id),
  FOREIGN KEY (fromUnit) REFERENCES unit(id),
  FOREIGN KEY (toUnit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS substitution (
  id SERIAL PRIMARY KEY,
  firstIngredient BIGINT NOT NULL,
  secondIngredient BIGINT NOT NULL,
  note text NOT NULL,
  FOREIGN KEY (firstIngredient) REFERENCES ingredient(id),
  FOREIGN KEY (secondIngredient) REFERENCES ingredient(id));

CREATE TABLE IF NOT EXISTS recipe (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  servings INT NOT NULL,
  mainImage TEXT,
  source TEXT);

CREATE TABLE IF NOT EXISTS recipe_ingredient (
  id SERIAL PRIMARY KEY,
  recipeId BIGINT NOT NULL,
  ingredientId BIGINT NOT NULL,
  displayOrder INT NOT NULL,
  unit BIGINT NOT NULL,
  quantity NUMERIC NOT NULL,
  FOREIGN KEY (recipeId) REFERENCES recipe(id),
  FOREIGN KEY (ingredientId) REFERENCES ingredient(id),
  FOREIGN KEY (unit) REFERENCES unit(id));

CREATE TABLE IF NOT EXISTS step (
  id SERIAL PRIMARY KEY,
  recipeId BIGINT NOT NULL,
  displayOrder INT NOT NULL,
  description TEXT NOT NULL,
  imageLocation TEXT,
  FOREIGN KEY (recipeId) REFERENCES recipe(id));

CREATE TABLE IF NOT EXISTS image (
  id SERIAL PRIMARY KEY,
  recipeId BIGINT NOT NULL,
  imageLocation TEXT NOT NULL,
  FOREIGN KEY (recipeId) REFERENCES recipe(id));

