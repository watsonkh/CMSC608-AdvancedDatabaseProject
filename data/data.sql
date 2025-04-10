INSERT into unit (name, unitType, notation) VALUES
  ('teaspoon', 'volume', 'tsp'),
  ('tablespoon', 'volume', 'tbsp'),
  ('fluid ounce', 'volume', 'fl oz'),
  ('cup', 'volume', 'cup'),
  ('pint', 'volume', 'pt'),
  ('quart', 'volume', 'qt'),
  ('gallon', 'volume', 'gal'),
  ('milliliter', 'volume', 'ml'),
  ('liter', 'volume', 'l'),
  ('gram', 'mass', 'g'),
  ('kilogram', 'mass', 'kg'),
  ('ounce', 'mass', 'oz'),
  ('pound', 'mass', 'lb'),
  ('millimeter', 'length', 'mm'),
  ('centimeter', 'length', 'cm'),
  ('meter', 'length', 'm'),
  ('inch', 'length', 'in'),
  ('foot', 'length', 'ft'),
  ('yard', 'length', 'yd'),
  ('mile', 'length', 'mi'),
  ('14-ounce can', 'count', '14oz can'),
  ('clove', 'count', 'clove'),
  ('knob', 'count', 'knob'),
  ('handful', 'count', 'handful'),
  ('dash', 'count', 'dash'),
  ('rib', 'count', 'rib'),
  ('sprig', 'count', 'sprig'),
  ('whole', 'count', 'whole'),
  ('bunch', 'count', 'bunch'),
  ('slice', 'count', 'slice');

INSERT into unit_conversion (fromUnit, toUnit, ratio) VALUES
  ((SELECT id FROM unit WHERE notation = 'tsp'), (SELECT id FROM unit WHERE notation = 'ml'), 5),           -- 1 tsp = 5 mL
  ((SELECT id FROM unit WHERE notation = 'tsp'), (SELECT id FROM unit WHERE notation = 'l'), 0.005),        -- 1 tsp = 0.005 L
  ((SELECT id FROM unit WHERE notation = 'tbsp'), (SELECT id FROM unit WHERE notation = 'tsp'), 3),         -- 1 tbsp = 3 tsp
  ((SELECT id FROM unit WHERE notation = 'fl oz'), (SELECT id FROM unit WHERE notation = 'tsp'), 6),        -- 1 fl oz = 6 tsp
  ((SELECT id FROM unit WHERE notation = 'fl oz'), (SELECT id FROM unit WHERE notation = 'tbsp'), 2),       -- 1 fl oz = 2 tbsp
  ((SELECT id FROM unit WHERE notation = 'cup'), (SELECT id FROM unit WHERE notation = 'fl oz'), 8),        -- 1 cup = 8 fl oz
  ((SELECT id FROM unit WHERE notation = 'cup'), (SELECT id FROM unit WHERE notation = 'ml'), 240),         -- 1 cup = 240 mL
  ((SELECT id FROM unit WHERE notation = 'cup'), (SELECT id FROM unit WHERE notation = 'l'), 0.24),         -- 1 cup = 0.24 L
  ((SELECT id FROM unit WHERE notation = 'pt'), (SELECT id FROM unit WHERE notation = 'cup'), 2),           -- 1 pt = 2 cup
  ((SELECT id FROM unit WHERE notation = 'pt'), (SELECT id FROM unit WHERE notation = 'ml'), 480),          -- 1 pt = 480 mL
  ((SELECT id FROM unit WHERE notation = 'pt'), (SELECT id FROM unit WHERE notation = 'l'), 0.48),          -- 1 pt = 0.48 L
  ((SELECT id FROM unit WHERE notation = 'qt'), (SELECT id FROM unit WHERE notation = 'pt'), 2),            -- 1 qt = 2 pt
  ((SELECT id FROM unit WHERE notation = 'qt'), (SELECT id FROM unit WHERE notation = 'cup'), 4),           -- 1 qt = 4 cup
  ((SELECT id FROM unit WHERE notation = 'qt'), (SELECT id FROM unit WHERE notation = 'ml'), 960),          -- 1 qt = 960 mL
  ((SELECT id FROM unit WHERE notation = 'qt'), (SELECT id FROM unit WHERE notation = 'l'), 0.96),          -- 1 qt = 0.96 L
  ((SELECT id FROM unit WHERE notation = 'gal'), (SELECT id FROM unit WHERE notation = 'qt'), 4),           -- 1 gal = 4 qt
  ((SELECT id FROM unit WHERE notation = 'gal'), (SELECT id FROM unit WHERE notation = 'pt'), 8),           -- 1 gal = 8 pt
  ((SELECT id FROM unit WHERE notation = 'gal'), (SELECT id FROM unit WHERE notation = 'cup'),16),          -- 1 gal =16 cup
  ((SELECT id FROM unit WHERE notation = 'gal'), (SELECT id FROM unit WHERE notation = 'ml'),3840),         -- 1 gal=3840 mL
  ((SELECT id FROM unit WHERE notation = 'gal'), (SELECT id FROM unit WHERE notation = 'l'),3.84),          -- 1 gal=3.84 L
  ((SELECT id FROM unit WHERE notation = 'g'), (SELECT id FROM unit WHERE notation = 'kg'), 0.001),         -- 1 g = 0.001 kg
  ((SELECT id FROM unit WHERE notation = 'g'), (SELECT id FROM unit WHERE notation = 'oz'), 0.03527396),    -- 1 g = 0.03527396 oz
  ((SELECT id FROM unit WHERE notation = 'g'), (SELECT id FROM unit WHERE notation = 'lb'), 0.00220462),    -- 1 g = 0.00220462 lb
  ((SELECT id FROM unit WHERE notation = 'kg'), (SELECT id FROM unit WHERE notation = 'g'), 1000),          -- 1 kg = 1000 g
  ((SELECT id FROM unit WHERE notation = 'kg'), (SELECT id FROM unit WHERE notation = 'oz'), 35.27396);     -- 1 kg= 35.27396 oz
