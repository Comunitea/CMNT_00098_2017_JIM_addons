--
-- PARAMETERIZATION FIELD
--

CREATE TABLE public.parameterization_field (
    jim_id bigint NOT NULL,
    name json NOT NULL
);

ALTER TABLE public.parameterization_field OWNER TO postgres;
ALTER TABLE ONLY public.parameterization_field ADD CONSTRAINT parameterization_field_pkey PRIMARY KEY (jim_id);

--
-- PARAMETERIZATION VALUE
--

CREATE TABLE public.parameterization_value (
    jim_id bigint NOT NULL,
    name json NOT NULL,
    fields json
);

ALTER TABLE public.parameterization_value OWNER TO postgres;
ALTER TABLE ONLY public.parameterization_value ADD CONSTRAINT parameterization_value_pkey PRIMARY KEY (jim_id);

--
-- PRODUCT PARAMETERIZATION
--

CREATE TABLE public.product_parameterization (
    jim_id bigint NOT NULL,
    product_id bigint NOT NULL,
    parameters json NOT NULL
);

ALTER TABLE public.product_parameterization OWNER TO postgres;
ALTER TABLE ONLY public.product_parameterization ADD CONSTRAINT product_parameterization_pkey PRIMARY KEY (jim_id);
ALTER TABLE ONLY public.product_parameterization ADD CONSTRAINT product_id FOREIGN KEY (product_id) REFERENCES public.product(jim_id) ON DELETE CASCADE;