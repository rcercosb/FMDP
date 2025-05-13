DROP TABLE IF EXISTS wildfires;
DROP TABLE IF EXISTS heat_source;
DROP TABLE IF EXISTS arboreous_fuel;
DROP TABLE IF EXISTS herbaceous_fuel;
DROP TABLE IF EXISTS ligneous_fuel;
DROP TABLE IF EXISTS non_forested_fuel;
DROP TABLE IF EXISTS type_of_fuel;
DROP TABLE IF EXISTS type_of_wildfire;

------------------------
-- INCENDIS FORESTALS --
------------------------

-- Creates a table where to store the rows with repeated final_code
CREATE TABLE wildfires_repeated_final_code (gid integer NOT NULL, final_code character varying(11), municipality character varying(80), wildfire_date date, geom geometry);

-- Populates the previous table with a single row for each repeated final_code
INSERT INTO wildfires_repeated_final_code
SELECT MIN(gid) AS gid, final_code, MIN(municipality) AS municipality, MIN(wildfire_date) AS wildfire_date, ST_UNION(ST_MakeValid(geom)) as geom
FROM wildfires_1986_2023
GROUP BY final_code
HAVING COUNT(final_code) > 1;

-- Removes all the rows of the wildfires_1986_2023 table with a repeated final_code
DELETE FROM wildfires_1986_2023
WHERE final_code IN (SELECT final_code FROM public.wildfires_repeated_final_code);

-- Inserts the wildfires_repeated_final_code rows into the wildfires_1986_2023 table
INSERT INTO wildfires_1986_2023
SELECT *
FROM wildfires_repeated_final_code;

-- Removes the column final_code
ALTER TABLE wildfires_1986_2023
DROP COLUMN final_code;

-- Creates a table that relates the rows of the wildfires_1986_2023 table with the official names of the municipalities where the wildfires occurred
-- There could be multiple municipalities affected by a wildfire, so the municipalities are given a similarity index
SELECT r.*
INTO public.similarity_index_50000
FROM (
	SELECT public.wildfires_1986_2023.gid,
			public.wildfires_1986_2023.municipality,
			public.municipis_50000.nommuni,
			similarity(municipality, nommuni) AS sim
	FROM public.wildfires_1986_2023, public.municipis_50000
	WHERE ST_CONTAINS(public.municipis_50000.geom, public.wildfires_1986_2023.geom) OR -- the municipality contains the wildfire
			ST_CONTAINS(public.wildfires_1986_2023.geom, public.municipis_50000.geom) OR -- the wildfire contains the municipality
			ST_OVERLAPS(public.municipis_50000.geom, public.wildfires_1986_2023.geom) -- one overlaps with the other
) r;

-- Creates a table that relates the gid with the most similar municipality name
SELECT r.*
INTO public.most_similar_50000
FROM (
	SELECT gid, municipality, nommuni
	FROM public.similarity_index_50000
	WHERE (gid, sim) IN (SELECT gid, MAX(sim) FROM public.similarity_index_50000 GROUP BY gid)
) r;

-- Replaces the municipality names
UPDATE public.wildfires_1986_2023
SET municipality = public.most_similar_50000.nommuni
FROM public.most_similar_50000
WHERE public.wildfires_1986_2023.gid = public.most_similar_50000.gid;

----------
-- EGIF --
----------

-------------------------------------------------------------------------------
-- pif_location_timestamps: Pif & pif_localizacion & pif_tiempos & Municipio --
-------------------------------------------------------------------------------

-- Creates a table which is the product of joining the wildfires ID's table with the tables of the locations, the municipality names and the timestamps
SELECT r.*
INTO public.pif_location_timestamps
FROM(
	SELECT public."Pif"."NumeroParte" AS report_id,
			public.pif_tiempos.deteccion AS detection_timestamp,
			public.pif_tiempos.extinguido AS extinction_timestamp,
			public."Municipio"."Nombre" AS municipality,
			public.pif_localizacion.hoja,
			public.pif_localizacion.cuadricula
	FROM public."Pif"
	INNER JOIN public.pif_tiempos
	ON public."Pif"."NumeroParte" = public.pif_tiempos.numeroparte -- by the report ID
	INNER JOIN public.pif_localizacion
	ON public."Pif"."NumeroParte" = public.pif_localizacion.numeroparte -- by the report ID
	INNER JOIN public."Municipio"
	ON pif_localizacion.idcomunidad = public."Municipio"."IdComunidad" -- by the community ID
	AND pif_localizacion.idprovincia = public."Municipio"."IdProvincia" -- by the province ID 
	AND pif_localizacion.idmunicipio = public."Municipio"."IdMunicipio" -- by the municipality ID
	WHERE public."Municipio"."IdComunidad" = 2 AND -- 2: Catalonia
			EXTRACT(year FROM public.pif_tiempos.deteccion) >= 1986 AND
			EXTRACT(year FROM public.pif_tiempos.deteccion) <= 2023 -- for the wildfires that we have its geometry
) r;

-------------------------------
-- military_map: cuadriculas --
-------------------------------

-- Creates a table, which is the product of modifying the cuadriculas table
SELECT r.*
INTO public.military_map
FROM(
	SELECT SUBSTRING(descriptio FROM '%HOJA = #"____#"<br%' FOR '#') AS "page",
			"name" AS cell,
			geom
	FROM public.cuadriculas
) r;

----------------------------------------------------------------------------------
-- pif_location_timestamps_military_map: pif_location_timestamps & military_map --
----------------------------------------------------------------------------------

SELECT r.*
INTO public.pif_location_timestamps_military_map
FROM (
	SELECT public.pif_location_timestamps.report_id,
			public.pif_location_timestamps.detection_timestamp,
			public.pif_location_timestamps.extinction_timestamp,
			public.pif_location_timestamps.municipality,
			ST_Transform(ST_Force2D(public.military_map.geom), 25831) AS geom -- 25831 (wildfires_1986_2023's SRID)
	FROM public.pif_location_timestamps
	INNER JOIN public.military_map
	ON public.pif_location_timestamps.hoja = public.military_map."page" AND
		public.pif_location_timestamps.cuadricula = public.military_map.cell
) r;

-- Creates a table that relates the rows of the pif_location_timestamps_military_map table with the official names of the municipalities where the wildfires occurred
-- There could be multiple municipalities affected by a wildfire, so the municipalities are given a similarity index
SELECT r.*
INTO public.similarity_index_250000
FROM (
	SELECT public.pif_location_timestamps_military_map.report_id,
			public.pif_location_timestamps_military_map.municipality,
			public.municipis_250000.nommuni,
			similarity(municipality, nommuni) AS sim
	FROM public.pif_location_timestamps_military_map, public.municipis_250000
	WHERE ST_CONTAINS(public.municipis_250000.geom, public.pif_location_timestamps_military_map.geom) OR -- the municipality contains the cell
			ST_CONTAINS(public.pif_location_timestamps_military_map.geom, public.municipis_250000.geom) OR -- the cell contains the municipality
			ST_OVERLAPS(public.municipis_250000.geom, public.pif_location_timestamps_military_map.geom) -- one overlaps with the other
) r;

-- Creates a table that relates the report_id with the most similar municipality name
SELECT r.*
INTO public.most_similar_250000
FROM (
	SELECT report_id, municipality, nommuni
	FROM public.similarity_index_250000
	WHERE (report_id, sim) IN (SELECT report_id, MAX(sim) FROM public.similarity_index_250000 GROUP BY report_id)
) r;

-- Replaces the municipality names
UPDATE public.pif_location_timestamps_military_map
SET municipality = public.most_similar_250000.nommuni
FROM public.most_similar_250000
WHERE public.pif_location_timestamps_military_map.report_id = public.most_similar_250000.report_id;

--------------------------------------------------------------------------------
-- wildfires_egif: wildfires_1986_2023 & pif_location_timestamps_military_map --
--------------------------------------------------------------------------------

DROP SEQUENCE IF EXISTS wildfires_egif_seq;

CREATE SEQUENCE wildfires_egif_seq INCREMENT 1 START 1;

SELECT r.*
INTO public.wildfires_egif
FROM(
	SELECT nextval('wildfires_egif_seq') AS gid,
			public.wildfires_1986_2023.gid AS wildfires_1986_2023_gid,
			public.pif_location_timestamps_military_map.municipality,
			public.pif_location_timestamps_military_map.detection_timestamp,
			public.pif_location_timestamps_military_map.extinction_timestamp,
			public.pif_location_timestamps_military_map.report_id
	FROM public.wildfires_1986_2023
	INNER JOIN public.pif_location_timestamps_military_map
	ON public.wildfires_1986_2023.municipality = public.pif_location_timestamps_military_map.municipality AND -- by the municipality name
		public.wildfires_1986_2023.wildfire_date = public.pif_location_timestamps_military_map.detection_timestamp::date -- by the wildfire date
	ORDER BY public.wildfires_1986_2023.gid, public.pif_location_timestamps_military_map.report_id
) r;

-- Deletes one of the two rows with the same wildfires_1986_2023_gid and report_id
DELETE FROM public.wildfires_egif
WHERE public.wildfires_egif.gid IN (
	SELECT MAX(gid)
	FROM public.wildfires_egif
	WHERE (wildfires_1986_2023_gid, report_id) IN (
		SELECT wildfires_1986_2023_gid, report_id
		FROM public.wildfires_egif
		GROUP BY wildfires_1986_2023_gid, report_id
		HAVING COUNT(*) > 1
	)
);

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- heat_source: pif_causa & CodInvestigacionCausa & CodCertidumbreCausa & CodAutorizacionActividad & CodGradoResponsabilidad & CodCausa & CodMotivacion	& CodCausante & CodClaseDia --
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

SELECT r.*
INTO public.heat_source
FROM(
	SELECT public.pif_causa.numeroparte AS report_id,
			public."CodInvestigacionCausa"."Descripcion" AS investigation,
			public."CodCertidumbreCausa"."Descripcion" AS certainty,
			public."CodAutorizacionActividad"."Descripcion" AS "authorization",
			public."CodGradoResponsabilidad"."Descripcion" AS responsibility,
			public."CodCausa"."Descripcion" AS cause,
			public."CodMotivacion"."Descripcion" AS motivation,
			public."CodCausante"."Descripcion" AS identification,
			public."CodClaseDia"."Descripcion" AS type_of_day
	FROM public.pif_causa
	LEFT JOIN public."CodInvestigacionCausa"
	ON public."CodInvestigacionCausa"."IdIdioma" = 1 AND -- Catalan
		public.pif_causa.idinvestigacioncausa = public."CodInvestigacionCausa"."IdInvestigacionCausa" -- by the investigation ID
	LEFT JOIN public."CodCertidumbreCausa"
	ON public."CodCertidumbreCausa"."IdIdioma" = 1 AND
		public.pif_causa.idcertidumbrecausa = public."CodCertidumbreCausa"."IdCertidumbreCausa" -- by the certainty ID
	LEFT JOIN public."CodAutorizacionActividad"
	ON public."CodAutorizacionActividad"."IdIdioma" = 1 AND 
		public.pif_causa.idautorizacionactividad = public."CodAutorizacionActividad"."IdAutorizacionActividad" -- by the authorization ID
	LEFT JOIN public."CodGradoResponsabilidad"
	ON public."CodGradoResponsabilidad"."IdIdioma" = 1 AND
		public.pif_causa.idgradoresponsabilidad = public."CodGradoResponsabilidad"."IdGradoResponsabilidad" -- by the responsibility ID
	LEFT JOIN public."CodCausa"
	ON public."CodCausa"."IdIdioma" = 1 AND
		public.pif_causa.idcausa = public."CodCausa"."IdCausa" -- by the cause ID
	LEFT JOIN public."CodMotivacion"
	ON public."CodMotivacion"."IdIdioma" = 1 AND
		public.pif_causa.idmotivacion = public."CodMotivacion"."IdMotivacion" -- by the motivation ID
	LEFT JOIN public."CodCausante"
	ON public."CodCausante"."IdIdioma" = 1 AND
		public.pif_causa.idcausante = public."CodCausante"."IdCausante" -- by the identification ID
	LEFT JOIN public."CodClaseDia"
	ON public."CodClaseDia"."IdIdioma" = 1 AND
		public.pif_causa.idclasedia = public."CodClaseDia"."IdClaseDia" -- by the type of day ID
	WHERE public.pif_causa.numeroparte IN (SELECT public.wildfires_egif.report_id FROM public.wildfires_egif) -- for the wildfires that we have its geometry
) r;

-- LEFT JOIN because we want a row for each matching wildfire, even if some columns are empty

---------------------------------------------------------------------
-- arboreous_fuel: RelArboladoAfectadoParteMonte & CodEspecieArbol --
---------------------------------------------------------------------

SELECT r.*
INTO public.arboreous_fuel
FROM(
	SELECT public."RelArboladoAfectadoParteMonte"."NumeroParte" AS report_id,
			public."RelArboladoAfectadoParteMonte"."IdParteMonte" AS mountain_report_id,
			public."CodEspecieArbol"."Descripcion" AS species,
			public."RelArboladoAfectadoParteMonte"."FCC" AS canopy_cover, -- FCC: Fracción de Cabida de Cubierta (CAST) = Canopy Cover (ENG) [https://www.termcat.cat/oc/cercaterm/fitxa/MzM0ODU3OQ%3D%3D]
			public."RelArboladoAfectadoParteMonte"."EstadoMasaR" AS reforested, -- R: Reforestado (CAST) = Reforested (ENG) [https://www.termcat.cat/oc/cercaterm/fitxa/NDE2MzA4]
			public."RelArboladoAfectadoParteMonte"."EstadoMasaMB" AS thicket, -- MB: Monte Bravo (CAST) = Thicket (ENG) [https://www.termcat.cat/oc/cercaterm/fitxa/MjA2NTI5]
			public."RelArboladoAfectadoParteMonte"."EstadoMasaL" AS pole_plantation, -- L: Latizal (CAST) = Pole Plantation (ENG) [https://www.termcat.cat/oc/cercaterm/fitxa/MjA2NTI1]
			public."RelArboladoAfectadoParteMonte"."EstadoMasaF" AS high_forest, -- F: Fustal (CAST) = High Forest (ENG) [https://www.termcat.cat/oc/cercaterm/fitxa/MzM1MDgwMg%3D%3D]
			public."RelArboladoAfectadoParteMonte"."Superficie" AS area
	FROM public."RelArboladoAfectadoParteMonte"
	INNER JOIN public."CodEspecieArbol" ON public."RelArboladoAfectadoParteMonte"."IdEspecie" = public."CodEspecieArbol"."IdEspecie"  -- by the tree's species ID
	WHERE public."RelArboladoAfectadoParteMonte"."NumeroParte" IN (SELECT public.wildfires_egif.report_id FROM public.wildfires_egif)
) r;

--------------------------------------------------------------------------
-- ligneous_fuel: RelNoArboladoLeniosoParteMonte & CodNoArboladoLenioso --
--------------------------------------------------------------------------

SELECT r.*
INTO public.ligneous_fuel
FROM(
	SELECT public."RelNoArboladoLeniosoParteMonte"."NumeroParte" AS report_id,
			public."RelNoArboladoLeniosoParteMonte"."IdParteMonte" AS mountain_report_id,
			public."RelNoArboladoLeniosoParteMonte"."Superficie" AS area,
			public."CodNoArboladoLenioso"."Descripcion" AS "type"
	FROM public."RelNoArboladoLeniosoParteMonte"
	INNER JOIN public."CodNoArboladoLenioso"
	ON public."CodNoArboladoLenioso"."IdIdioma" = 1 AND 
		public."RelNoArboladoLeniosoParteMonte"."IdNoArboladoLenioso" = public."CodNoArboladoLenioso"."IdNoArboladoLenioso" -- by the ligneous ID
	WHERE public."RelNoArboladoLeniosoParteMonte"."NumeroParte" IN (SELECT public.wildfires_egif.report_id FROM public.wildfires_egif)
) r;

------------------------------------------------------------------------------
-- herbaceous_fuel: RelNoArboladoHerbaceoParteMonte & CodNoArboladoHerbaceo --
------------------------------------------------------------------------------

SELECT r.*
INTO public.herbaceous_fuel
FROM(
	SELECT public."RelNoArboladoHerbaceoParteMonte"."NumeroParte" AS report_id,
			public."RelNoArboladoHerbaceoParteMonte"."IdParteMonte" AS mountain_report_id,
			public."RelNoArboladoHerbaceoParteMonte"."Superficie" AS area,
			public."CodNoArboladoHerbaceo"."Descripcion" AS "type"
	FROM public."RelNoArboladoHerbaceoParteMonte"
	INNER JOIN public."CodNoArboladoHerbaceo"
	ON public."CodNoArboladoHerbaceo"."IdIdioma" = 1 AND
		public."RelNoArboladoHerbaceoParteMonte"."IdNoArboladoHerbaceo" = public."CodNoArboladoHerbaceo"."IdNoArboladoHerbaceo" -- by the herbaceous ID
	WHERE public."RelNoArboladoHerbaceoParteMonte"."NumeroParte" IN (SELECT public.wildfires_egif.report_id FROM public.wildfires_egif)
) r;

------------------------------------------------------------------------
-- non_forested_fuel: RelNoForestalAfectadoParteMonte & CodNoForestal --
------------------------------------------------------------------------

SELECT r.*
INTO public.non_forested_fuel
FROM(
	SELECT public."RelNoForestalAfectadoParteMonte"."NumeroParte" AS report_id,
			public."RelNoForestalAfectadoParteMonte"."IdParteMonte" AS mountain_report_id,
			public."RelNoForestalAfectadoParteMonte"."Superficie" AS area,
			public."CodNoForestal"."Descripcion" AS "type"
	FROM public."RelNoForestalAfectadoParteMonte"
	INNER JOIN public."CodNoForestal"
	ON public."CodNoForestal"."IdIdioma" = 1 AND
		public."RelNoForestalAfectadoParteMonte"."IdNoForestal" = public."CodNoForestal"."IdNoForestal" -- by the non forested ID
	WHERE public."RelNoForestalAfectadoParteMonte"."NumeroParte" IN (SELECT public.wildfires_egif.report_id FROM public.wildfires_egif)
) r;

----------------------------------------------------------------
-- type_of_fuel: RelModeloCombustionPif & CodModeloCombustion --
----------------------------------------------------------------

SELECT r.*
INTO public.type_of_fuel
FROM(
	SELECT public."RelModeloCombustionPif"."NumeroParte" AS report_id,
			public."CodModeloCombustion"."Descripcion" AS "type"
	FROM public."RelModeloCombustionPif"
	INNER JOIN public."CodModeloCombustion"
	ON public."CodModeloCombustion"."IdIdioma" = 1 AND
		public."RelModeloCombustionPif"."IdModeloCombustion" = public."CodModeloCombustion"."IdModeloCombustion" -- by the combustion model ID
	WHERE public."RelModeloCombustionPif"."NumeroParte" IN (SELECT public.wildfires_egif.report_id FROM public.wildfires_egif)
) r;

------------------------------------------------------
-- type_of_wildfire: RelTipoFuegoPif & CodTipoFuego --
------------------------------------------------------

SELECT r.*
INTO public.type_of_wildfire
FROM(
	SELECT public."RelTipoFuegoPif"."NumeroParte" AS report_id,
			public."CodTipoFuego"."Descripcion" AS "type"
	FROM public."RelTipoFuegoPif"
	INNER JOIN public."CodTipoFuego"
	ON public."CodTipoFuego"."IdIdioma" = 1 AND
		public."RelTipoFuegoPif"."IdTipoFuego" = public."CodTipoFuego"."IdTipoFuego" -- by the wildfire type ID
	WHERE public."RelTipoFuegoPif"."NumeroParte" IN (SELECT public.wildfires_egif.report_id FROM public.wildfires_egif)
) r;

-- Creates a table of repeated wildfires_1986_2023_gid's
SELECT r.*
INTO public.wildfires_egif_repeated
FROM(
	SELECT DISTINCT public.wildfires_egif.wildfires_1986_2023_gid
	FROM public.wildfires_egif
	GROUP BY public.wildfires_egif.wildfires_1986_2023_gid
	HAVING COUNT(public.wildfires_egif.wildfires_1986_2023_gid) > 1
	ORDER BY wildfires_1986_2023_gid
) r;

-----------------------------------------------------------------------------------------------------------------
-- wildfires_egif_areas: wildfires_egif & arboreous_fuel & ligneous_fuel & herbaceous_fuel & non_forested_fuel --
-----------------------------------------------------------------------------------------------------------------

-- Gets the arboreous, ligneous, herbaceous and non-forested burned area of each wildfire in wildfires_egif_repeated
SELECT r.*
INTO public.wildfires_egif_areas
FROM(
	SELECT public.wildfires_egif.wildfires_1986_2023_gid,
			public.wildfires_egif.detection_timestamp,
			public.wildfires_egif.extinction_timestamp,
			GREATEST(0, public.arboreous_fuel.area) AS area
	FROM public.wildfires_egif
	LEFT JOIN public.arboreous_fuel
	ON public.arboreous_fuel.report_id = public.wildfires_egif.report_id
	WHERE public.wildfires_egif.wildfires_1986_2023_gid IN (
		SELECT public.wildfires_egif_repeated.wildfires_1986_2023_gid
		FROM public.wildfires_egif_repeated
	)
	UNION
	SELECT public.wildfires_egif.wildfires_1986_2023_gid,
			public.wildfires_egif.detection_timestamp,
			public.wildfires_egif.extinction_timestamp,
			GREATEST(0, public.ligneous_fuel.area) AS area
	FROM public.wildfires_egif
	LEFT JOIN public.ligneous_fuel
	ON public.ligneous_fuel.report_id = public.wildfires_egif.report_id
	WHERE public.wildfires_egif.wildfires_1986_2023_gid IN (
		SELECT public.wildfires_egif_repeated.wildfires_1986_2023_gid
		FROM public.wildfires_egif_repeated
	)
	UNION
	SELECT public.wildfires_egif.wildfires_1986_2023_gid,
			public.wildfires_egif.detection_timestamp,
			public.wildfires_egif.extinction_timestamp,
			GREATEST(0, public.herbaceous_fuel.area) AS area
	FROM public.wildfires_egif
	LEFT JOIN public.herbaceous_fuel
	ON public.herbaceous_fuel.report_id = public.wildfires_egif.report_id
	WHERE public.wildfires_egif.wildfires_1986_2023_gid IN (
		SELECT public.wildfires_egif_repeated.wildfires_1986_2023_gid
		FROM public.wildfires_egif_repeated
	)
	UNION
	SELECT public.wildfires_egif.wildfires_1986_2023_gid,
			public.wildfires_egif.detection_timestamp,
			public.wildfires_egif.extinction_timestamp,
			GREATEST(0, public.non_forested_fuel.area) AS area
	FROM public.wildfires_egif
	LEFT JOIN public.non_forested_fuel
	ON public.non_forested_fuel.report_id = public.wildfires_egif.report_id
	WHERE public.wildfires_egif.wildfires_1986_2023_gid IN (
		SELECT public.wildfires_egif_repeated.wildfires_1986_2023_gid
		FROM public.wildfires_egif_repeated
	)
	ORDER BY wildfires_1986_2023_gid, detection_timestamp
) r;

-- Creates a table with the sum of the areas of each triplet of wildfires_1986_2023_gid, detection_timestamp and extinction_timestamp
-- If it's the same wildfires_1986_2023_gid and the timestamps match to the second, they are the same wildfire
SELECT r.*
INTO public.wildfires_egif_areas_sum
FROM(
	SELECT public.wildfires_egif_areas.wildfires_1986_2023_gid,
			public.wildfires_egif_areas.detection_timestamp,
			public.wildfires_egif_areas.extinction_timestamp,
			SUM(public.wildfires_egif_areas.area)
	FROM public.wildfires_egif_areas
	GROUP BY wildfires_1986_2023_gid, detection_timestamp, extinction_timestamp
	ORDER BY wildfires_1986_2023_gid, detection_timestamp, extinction_timestamp
) r;

-- Creates a table with the smaller areas of each wildfires_1986_2023_gid
SELECT r.*
INTO public.wildfires_egif_smaller
FROM(
	SELECT *
	FROM public.wildfires_egif_areas_sum
	WHERE (wildfires_1986_2023_gid, "sum") NOT IN (
		SELECT wildfires_1986_2023_gid, MAX("sum")
		FROM public.wildfires_egif_areas_sum
		GROUP BY wildfires_1986_2023_gid
		ORDER BY wildfires_1986_2023_gid
	)
) r;

-- Creates a table with the report_id's of the smaller areas of each wildfires_1986_2023_gid
SELECT r.*
INTO public.wildfires_egif_smaller_report_id
FROM(
	SELECT report_id
	FROM wildfires_egif
	WHERE (wildfires_1986_2023_gid, detection_timestamp, extinction_timestamp) IN (
		SELECT wildfires_1986_2023_gid, detection_timestamp, extinction_timestamp
		FROM public.wildfires_egif_smaller
	)
) r;

-- Deletes the report_id's with smaller areas
-- The report_id's left are the ones with the biggest area, which are the wildfires most likely to have been delimited (the ones in wildfires_1986_2023)
DELETE FROM wildfires_egif
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

DELETE FROM heat_source
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

DELETE FROM arboreous_fuel
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

DELETE FROM ligneous_fuel
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

DELETE FROM herbaceous_fuel
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

DELETE FROM non_forested_fuel
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

DELETE FROM type_of_fuel
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

DELETE FROM type_of_wildfire
WHERE report_id IN (
	SELECT *
	FROM public.wildfires_egif_smaller_report_id
);

-- Deletes the no longer useful tables
DROP TABLE IF EXISTS "CodAutorizacionActividad";
DROP TABLE IF EXISTS "CodCausa";
DROP TABLE IF EXISTS "CodCausante";
DROP TABLE IF EXISTS "CodCertidumbreCausa";
DROP TABLE IF EXISTS "CodClaseDia";
DROP TABLE IF EXISTS "CodEspecieArbol";
DROP TABLE IF EXISTS "CodEstacionMeteorologica";
DROP TABLE IF EXISTS "CodGradoResponsabilidad";
DROP TABLE IF EXISTS "CodIdioma";
DROP TABLE IF EXISTS "CodInvestigacionCausa";
DROP TABLE IF EXISTS "CodModeloCombustion";
DROP TABLE IF EXISTS "CodMotivacion";
DROP TABLE IF EXISTS "CodNoArboladoHerbaceo";
DROP TABLE IF EXISTS "CodNoArboladoLenioso";
DROP TABLE IF EXISTS "CodNoForestal";
DROP TABLE IF EXISTS "CodTipoFuego";
DROP TABLE IF EXISTS "ComarcaIsla";
DROP TABLE IF EXISTS "Comunidad";
DROP TABLE IF EXISTS "EntidadMenor";
DROP TABLE IF EXISTS "Municipio";
DROP TABLE IF EXISTS "ParteMonte";
DROP TABLE IF EXISTS "Pif";
DROP TABLE IF EXISTS "Provincia";
DROP TABLE IF EXISTS "RelArboladoAfectadoParteMonte";
DROP TABLE IF EXISTS "RelAsociadoPif";
DROP TABLE IF EXISTS "RelModeloCombustionPif";
DROP TABLE IF EXISTS "RelNoArboladoHerbaceoParteMonte";
DROP TABLE IF EXISTS "RelNoArboladoLeniosoParteMonte";
DROP TABLE IF EXISTS "RelNoForestalAfectadoParteMonte";
DROP TABLE IF EXISTS "RelTipoFuegoPif";
DROP TABLE IF EXISTS "cuadriculas";
DROP TABLE IF EXISTS "military_map";
DROP TABLE IF EXISTS "most_similar_50000";
DROP TABLE IF EXISTS "most_similar_250000";
DROP TABLE IF EXISTS "municipis_250000";
DROP TABLE IF EXISTS "pif_causa";
DROP TABLE IF EXISTS "pif_condiciones";
DROP TABLE IF EXISTS "pif_localizacion";
DROP TABLE IF EXISTS "pif_location_timestamps";
DROP TABLE IF EXISTS "pif_location_timestamps_military_map";
DROP TABLE IF EXISTS "pif_tiempos";
DROP TABLE IF EXISTS "similarity_index_50000";
DROP TABLE IF EXISTS "similarity_index_250000";
DROP TABLE IF EXISTS "wildfires_egif_areas";
DROP TABLE IF EXISTS "wildfires_egif_areas_sum";
DROP TABLE IF EXISTS "wildfires_egif_repeated";
DROP TABLE IF EXISTS "wildfires_egif_smaller";
DROP TABLE IF EXISTS "wildfires_egif_smaller_report_id";
DROP TABLE IF EXISTS "wildfires_repeated_final_code";