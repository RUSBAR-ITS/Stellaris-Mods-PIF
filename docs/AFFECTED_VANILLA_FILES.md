# Affected Vanilla Files and Objects

This file lists the vanilla files and objects overridden by Planetary Infrastructure Framework.

PIF is built on the vanilla Stellaris **4.3.7** baseline. If another mod directly changes objects from the files listed below, it will most likely conflict with PIF.

## Summary

| Layer | Vanilla files | Objects |
|---|---:|---:|
| `common/districts` | 8 | 138 |
| `common/zones` | 5 | 120 |
| `common/zone_slots` | 2 | 27 |
| `common/buildings` | 26 | 490 |
| `common/pop_jobs` | 21 | 373 |
| **Total** | **62** | **1148** |

## Notes

- The list below contains the original vanilla files from which the overridden objects were taken.
- PIF does not use `replace_path`, but it overrides objects by using the same keys.
- A conflict is most likely if another mod also overrides one of the listed objects.

## Districts

Path: `common/districts`

| Vanilla file | Objects |
|---|---:|
| `common/districts/00_special_districts.txt` | 4 |
| `common/districts/00_urban_districts.txt` | 19 |
| `common/districts/01_arcology_districts.txt` | 5 |
| `common/districts/02_rural_districts.txt` | 9 |
| `common/districts/03_habitat_districts.txt` | 4 |
| `common/districts/04_ringworld_districts.txt` | 10 |
| `common/districts/05_wilderness_districts.txt` | 7 |
| `common/districts/06_swap_districts.txt` | 80 |

### `common/districts/00_special_districts.txt`

Objects: **4**

- `district_cosmogenesis_goverment`
- `district_cosmogenesis_world_logic`
- `district_cosmogenesis_world_science`
- `district_mindlink`

### `common/districts/00_urban_districts.txt`

Objects: **19**

- `district_battle_thrall`
- `district_city`
- `district_crashed_slaver_ship`
- `district_hive`
- `district_hive_1`
- `district_hive_2`
- `district_hive_3`
- `district_nexus`
- `district_nexus_1`
- `district_nexus_2`
- `district_nexus_3`
- `district_prison`
- `district_prison_industrial`
- `district_resort`
- `district_resort_1`
- `district_resort_2`
- `district_resort_3`
- `district_slave`
- `district_srw_commercial`

### `common/districts/01_arcology_districts.txt`

Objects: **5**

- `district_arcology_housing`
- `district_arcology_leisure`
- `district_arcology_urban_1`
- `district_arcology_urban_2`
- `district_arcology_urban_3`

### `common/districts/02_rural_districts.txt`

Objects: **9**

- `district_farming`
- `district_farming_uncapped`
- `district_generator`
- `district_generator_uncapped`
- `district_geothermal`
- `district_melting`
- `district_mining`
- `district_mining_uncapped`
- `district_polytechnic`

### `common/districts/03_habitat_districts.txt`

Objects: **4**

- `district_hab_energy`
- `district_hab_housing`
- `district_hab_mining`
- `district_hab_science`

### `common/districts/04_ringworld_districts.txt`

Objects: **10**

- `district_rw_city`
- `district_rw_commercial`
- `district_rw_farming`
- `district_rw_generator`
- `district_rw_hive`
- `district_rw_nexus`
- `district_rw_science`
- `district_rw_urban_1`
- `district_rw_urban_2`
- `district_rw_urban_3`

### `common/districts/05_wilderness_districts.txt`

Objects: **7**

- `district_craglands`
- `district_hollow_mountains`
- `district_hollow_mountains_uncapped`
- `district_orchard_forests`
- `district_orchard_forests_uncapped`
- `district_photosynthesis_fields`
- `district_photosynthesis_fields_uncapped`

### `common/districts/06_swap_districts.txt`

Objects: **80**

- `district_arcology_administrative`
- `district_arcology_arms_industry`
- `district_arcology_civilian_industry`
- `district_arcology_fortress`
- `district_arcology_mixed_industry`
- `district_arcology_organic_housing`
- `district_arcology_research`
- `district_arcology_research_engineering`
- `district_arcology_research_physics`
- `district_arcology_research_society`
- `district_arcology_spiritualist`
- `district_arcology_trade`
- `district_betharian_hive`
- `district_farming_exotic_gases`
- `district_farming_society`
- `district_generator_physics`
- `district_generator_volatile_motes`
- `district_hab_energy_exotic_gases`
- `district_hab_energy_volatile_motes`
- `district_hab_mining_rare_crystals`
- `district_hive_administrative`
- `district_hive_energy`
- `district_hive_exotic_gases`
- `district_hive_factory`
- `district_hive_food`
- `district_hive_fortress`
- `district_hive_foundry`
- `district_hive_industrial`
- `district_hive_mining`
- `district_hive_research`
- `district_hive_research_engineering`
- `district_hive_research_physics`
- `district_hive_research_society`
- `district_hive_spawning`
- `district_hive_trade`
- `district_hive_volatile_motes`
- `district_mining_betharian`
- `district_mining_engineering`
- `district_mining_physics`
- `district_mining_rare_crystals`
- `district_nexus_administrative`
- `district_nexus_betharian`
- `district_nexus_energy`
- `district_nexus_exotic_gases`
- `district_nexus_factory`
- `district_nexus_fortress`
- `district_nexus_foundry`
- `district_nexus_industrial`
- `district_nexus_mining`
- `district_nexus_organic_housing`
- `district_nexus_rare_crystals`
- `district_nexus_research`
- `district_nexus_research_engineering`
- `district_nexus_research_physics`
- `district_nexus_research_society`
- `district_nexus_spiritualist`
- `district_nexus_trade`
- `district_nexus_volatile_motes`
- `district_orders_demesne`
- `district_rare_crystals_hive`
- `district_resort_hunting_ground`
- `district_resort_museum`
- `district_resort_proving_grounds`
- `district_resort_restoration_enclave`
- `district_resort_spiritual_retreat`
- `district_resort_zoo`
- `district_ring_world_administrative`
- `district_ring_world_energy`
- `district_ring_world_factory`
- `district_ring_world_food`
- `district_ring_world_fortress`
- `district_ring_world_foundry`
- `district_ring_world_industrial`
- `district_ring_world_organic_housing`
- `district_ring_world_research`
- `district_ring_world_research_engineering`
- `district_ring_world_research_physics`
- `district_ring_world_research_society`
- `district_ring_world_spiritualist`
- `district_ring_world_trade`

## Zones

Path: `common/zones`

| Vanilla file | Objects |
|---|---:|
| `common/zones/00_zones.txt` | 38 |
| `common/zones/01_habitat_zones.txt` | 7 |
| `common/zones/02_special_zones.txt` | 3 |
| `common/zones/03_wilderness_zones.txt` | 10 |
| `common/zones/04_secondary_zones.txt` | 62 |

### `common/zones/00_zones.txt`

Objects: **38**

- `zone_agrarian_anglers`
- `zone_agrarian_urban`
- `zone_anglers`
- `zone_betharian`
- `zone_cosmogenesis_default`
- `zone_default`
- `zone_energy`
- `zone_exotic_gases`
- `zone_factory`
- `zone_food`
- `zone_fortress`
- `zone_foundry`
- `zone_industrial`
- `zone_machine_replication`
- `zone_minerals`
- `zone_minerals_physics`
- `zone_rare_crystals`
- `zone_research`
- `zone_research_engineering`
- `zone_research_physics`
- `zone_research_society`
- `zone_research_unity`
- `zone_resort`
- `zone_resort_entertainment`
- `zone_resort_grand_museum`
- `zone_resort_hunting_ground`
- `zone_resort_proving_grounds`
- `zone_resort_restoration_enclave`
- `zone_resort_spiritual_retreat`
- `zone_resort_zoo`
- `zone_spawning`
- `zone_subterranean_urban`
- `zone_trade`
- `zone_unity`
- `zone_unity_bio_trophy`
- `zone_unity_spiritualist`
- `zone_urban`
- `zone_volatile_motes`

### `common/zones/01_habitat_zones.txt`

Objects: **7**

- `zone_habitat_exotic_gases`
- `zone_habitat_hydroponics`
- `zone_habitat_knights`
- `zone_habitat_rare_crystals`
- `zone_habitat_research`
- `zone_habitat_research_unity`
- `zone_habitat_volatile_motes`

### `common/zones/02_special_zones.txt`

Objects: **3**

- `zone_broken_shackles_memorial`
- `zone_central_spire`
- `zone_payback_enlightenment`

### `common/zones/03_wilderness_zones.txt`

Objects: **10**

- `zone_energy_wilderness`
- `zone_food_wilderness`
- `zone_fortress_wilderness`
- `zone_foundry_wilderness`
- `zone_minerals_wilderness`
- `zone_research_unity_wilderness`
- `zone_research_wilderness`
- `zone_trade_wilderness`
- `zone_unity_wilderness`
- `zone_urban_wilderness`

### `common/zones/04_secondary_zones.txt`

Objects: **62**

- `zone_betharian_hive`
- `zone_betharian_nexus`
- `zone_energy_hive`
- `zone_energy_nexus`
- `zone_energy_ring_world`
- `zone_exotic_gases_hive`
- `zone_exotic_gases_nexus`
- `zone_factory_arcology`
- `zone_factory_hive`
- `zone_factory_nexus`
- `zone_factory_ring_world`
- `zone_food_hive`
- `zone_food_ring_world`
- `zone_fortress_arcology`
- `zone_fortress_hive`
- `zone_fortress_nexus`
- `zone_fortress_ring_world`
- `zone_foundry_arcology`
- `zone_foundry_hive`
- `zone_foundry_nexus`
- `zone_foundry_ring_world`
- `zone_industrial_arcology`
- `zone_industrial_hive`
- `zone_industrial_nexus`
- `zone_industrial_ring_world`
- `zone_minerals_hive`
- `zone_minerals_nexus`
- `zone_rare_crystals_hive`
- `zone_rare_crystals_nexus`
- `zone_research_arcology`
- `zone_research_engineering_arcology`
- `zone_research_engineering_hive`
- `zone_research_engineering_nexus`
- `zone_research_engineering_ring_world`
- `zone_research_hive`
- `zone_research_nexus`
- `zone_research_physics_arcology`
- `zone_research_physics_hive`
- `zone_research_physics_nexus`
- `zone_research_physics_ring_world`
- `zone_research_ring_world`
- `zone_research_society_arcology`
- `zone_research_society_hive`
- `zone_research_society_nexus`
- `zone_research_society_ring_world`
- `zone_spawning_hive`
- `zone_trade_arcology`
- `zone_trade_hive`
- `zone_trade_nexus`
- `zone_trade_ring_world`
- `zone_unity_arcology`
- `zone_unity_bio_trophy_arcology`
- `zone_unity_bio_trophy_nexus`
- `zone_unity_bio_trophy_ring_world`
- `zone_unity_hive`
- `zone_unity_nexus`
- `zone_unity_ring_world`
- `zone_unity_spiritualist_arcology`
- `zone_unity_spiritualist_nexus`
- `zone_unity_spiritualist_ring_world`
- `zone_volatile_motes_hive`
- `zone_volatile_motes_nexus`

## Zone Slots

Path: `common/zone_slots`

| Vanilla file | Objects |
|---|---:|
| `common/zone_slots/00_zone_slots.txt` | 22 |
| `common/zone_slots/01_habitat_zone_slots.txt` | 5 |

### `common/zone_slots/00_zone_slots.txt`

Objects: **22**

- `slot_arcology_urban_01`
- `slot_arcology_urban_02`
- `slot_arcology_urban_03`
- `slot_city_01`
- `slot_city_02`
- `slot_city_04`
- `slot_city_05`
- `slot_city_government`
- `slot_cosmogenesis_government`
- `slot_empty`
- `slot_energy`
- `slot_food`
- `slot_hive`
- `slot_minerals`
- `slot_nexus`
- `slot_polytechnic`
- `slot_resort_01`
- `slot_resort_02`
- `slot_resort_attraction_01`
- `slot_rw_urban_01`
- `slot_rw_urban_02`
- `slot_rw_urban_03`

### `common/zone_slots/01_habitat_zone_slots.txt`

Objects: **5**

- `slot_habitat_01`
- `slot_habitat_02`
- `slot_habitat_energy`
- `slot_habitat_minerals`
- `slot_habitat_research`

## Buildings

Path: `common/buildings`

| Vanilla file | Objects |
|---|---:|
| `common/buildings/00_capital_buildings.txt` | 20 |
| `common/buildings/01_pop_assembly_buildings.txt` | 19 |
| `common/buildings/02_government_buildings.txt` | 19 |
| `common/buildings/03_resource_buildings.txt` | 25 |
| `common/buildings/04_manufacturing_buildings.txt` | 20 |
| `common/buildings/05_research_buildings.txt` | 22 |
| `common/buildings/06_trade_buildings.txt` | 4 |
| `common/buildings/07_amenity_buildings.txt` | 17 |
| `common/buildings/08_unity_buildings.txt` | 38 |
| `common/buildings/09_army_buildings.txt` | 5 |
| `common/buildings/10_deposit_buildings.txt` | 5 |
| `common/buildings/11_primitive_buildings.txt` | 28 |
| `common/buildings/12_event_buildings.txt` | 12 |
| `common/buildings/13_fallen_empire_buildings.txt` | 46 |
| `common/buildings/14_branch_office_buildings.txt` | 35 |
| `common/buildings/15_overlord_holdings.txt` | 30 |
| `common/buildings/16_first_contact_buildings.txt` | 6 |
| `common/buildings/17_paragon_buildings.txt` | 3 |
| `common/buildings/18_astral_planes_buildings.txt` | 3 |
| `common/buildings/19_cosmic_storm_buildings.txt` | 11 |
| `common/buildings/20_machine_age_buildings.txt` | 32 |
| `common/buildings/21_grand_archive_buildings.txt` | 18 |
| `common/buildings/21_wilderness_buildings.txt` | 46 |
| `common/buildings/22_biogenesis_buildings.txt` | 2 |
| `common/buildings/22_extreme_frontiers_buildings.txt` | 3 |
| `common/buildings/23_shroud_buildings.txt` | 21 |

### `common/buildings/00_capital_buildings.txt`

Objects: **20**

- `building_capital`
- `building_colony_shelter`
- `building_deployment_post`
- `building_hab_capital`
- `building_hab_major_capital`
- `building_hab_system_capital`
- `building_hive_capital`
- `building_hive_major_capital`
- `building_imperial_capital`
- `building_imperial_hive_capital`
- `building_imperial_machine_capital`
- `building_machine_capital`
- `building_machine_major_capital`
- `building_machine_system_capital`
- `building_major_capital`
- `building_resort_capital`
- `building_resort_major_capital`
- `building_slave_capital`
- `building_slave_major_capital`
- `building_system_capital`

### `common/buildings/01_pop_assembly_buildings.txt`

Objects: **19**

- `building_automation_1`
- `building_automation_2`
- `building_automation_farmer_1`
- `building_automation_farmer_2`
- `building_automation_miner_1`
- `building_automation_miner_2`
- `building_automation_technician_1`
- `building_automation_technician_2`
- `building_clone_army_clone_vat`
- `building_clone_vats`
- `building_machine_assembly_complex`
- `building_machine_assembly_plant`
- `building_necrophage_elevation_chamber`
- `building_necrophage_house_of_apotheosis`
- `building_offspring_nest`
- `building_posthumous_employment_center`
- `building_robot_assembly_complex`
- `building_robot_assembly_plant`
- `building_spawning_pool`

### `common/buildings/02_government_buildings.txt`

Objects: **19**

- `building_center_of_guidance`
- `building_embassy`
- `building_gaiaseeders_1`
- `building_gaiaseeders_2`
- `building_gaiaseeders_3`
- `building_gaiaseeders_4`
- `building_gaiaseeders_pc_gaia`
- `building_grand_embassy`
- `building_hall_judgment`
- `building_noble_estates`
- `building_order_castle`
- `building_order_keep`
- `building_precinct_house`
- `building_psi_corps`
- `building_sentinel_posts`
- `building_slave_processing`
- `building_state_academy`
- `building_volcanic_forge_1`
- `building_volcanic_forge_2`

### `common/buildings/03_resource_buildings.txt`

Objects: **25**

- `building_baol_organic_plant`
- `building_bio_reactor`
- `building_bio_reactor_2`
- `building_energy_grid`
- `building_energy_nexus`
- `building_farming_districts_1`
- `building_farming_districts_2`
- `building_farming_districts_3`
- `building_farming_districts_4`
- `building_food_processing_center`
- `building_food_processing_facility`
- `building_generator_districts_1`
- `building_generator_districts_2`
- `building_generator_districts_3`
- `building_generator_districts_4`
- `building_generator_generic`
- `building_hydroponics_farm`
- `building_mine_generic`
- `building_mineral_purification_hub`
- `building_mineral_purification_plant`
- `building_mining_districts_1`
- `building_mining_districts_2`
- `building_mining_districts_3`
- `building_mining_districts_4`
- `building_resource_silo`

### `common/buildings/04_manufacturing_buildings.txt`

Objects: **20**

- `building_archaeo_refinery`
- `building_chemical_plant`
- `building_coordinated_fulfillment_center_1`
- `building_coordinated_fulfillment_center_2`
- `building_crystal_plant`
- `building_factory_1`
- `building_factory_2`
- `building_factory_3`
- `building_factory_efficiency_1`
- `building_factory_upkeep_1`
- `building_foundry_1`
- `building_foundry_2`
- `building_foundry_3`
- `building_foundry_efficiency_1`
- `building_foundry_upkeep_1`
- `building_ministry_production`
- `building_nanite_transmuter`
- `building_offworld_expedition_hub`
- `building_production_center`
- `building_refinery`

### `common/buildings/05_research_buildings.txt`

Objects: **22**

- `building_archaeostudies_faculty`
- `building_biolab_1`
- `building_biolab_2`
- `building_biolab_3`
- `building_engineering_facility_1`
- `building_engineering_facility_2`
- `building_engineering_facility_3`
- `building_institute`
- `building_physics_lab_1`
- `building_physics_lab_2`
- `building_physics_lab_3`
- `building_ranger_lodge`
- `building_research_efficiency_1`
- `building_research_lab_1`
- `building_research_lab_2`
- `building_research_lab_3`
- `building_research_upkeep_1`
- `building_shroud_observatory_1`
- `building_shroud_observatory_2`
- `building_shroud_observatory_3`
- `building_supercomputer`
- `building_vultaum_reality_computer`

### `common/buildings/06_trade_buildings.txt`

Objects: **4**

- `building_commercial_megaplex`
- `building_commercial_zone`
- `building_galactic_stock_exchange`
- `building_maintenance_depot`

### `common/buildings/07_amenity_buildings.txt`

Objects: **17**

- `building_communal_housing`
- `building_communal_housing_large`
- `building_drone_megastorage`
- `building_drone_storage`
- `building_expanded_warren`
- `building_hive_warren`
- `building_holo_theatres`
- `building_hyper_entertainment_forum`
- `building_luxury_residence`
- `building_medical_1`
- `building_medical_2`
- `building_medical_3`
- `building_overseer_homes`
- `building_paradise_dome`
- `building_toxic_bath`
- `building_toxic_bath_hive`
- `building_toxic_bath_machine`

### `common/buildings/08_unity_buildings.txt`

Objects: **38**

- `building_alpha_hub`
- `building_autochthon_monument`
- `building_autocurating_vault`
- `building_bureaucratic_1`
- `building_bureaucratic_2`
- `building_bureaucratic_3`
- `building_citadel_of_faith`
- `building_corporate_forum`
- `building_corporate_monument`
- `building_corporate_site`
- `building_corporate_vault`
- `building_galactic_memorial_1`
- `building_galactic_memorial_2`
- `building_galactic_memorial_3`
- `building_heritage_site`
- `building_hive_cluster`
- `building_hive_confluence`
- `building_hive_node`
- `building_holotemple`
- `building_hypercomms_forum`
- `building_league_offices`
- `building_network_junction`
- `building_organic_paradise`
- `building_organic_sanctuary`
- `building_sacred_nexus`
- `building_sacrificial_temple_1`
- `building_sacrificial_temple_2`
- `building_sacrificial_temple_3`
- `building_sensorium_1`
- `building_sensorium_2`
- `building_sensorium_3`
- `building_simulation_1`
- `building_simulation_2`
- `building_simulation_3`
- `building_system_conflux`
- `building_temple`
- `building_trophy_vault`
- `building_uplink_node`

### `common/buildings/09_army_buildings.txt`

Objects: **5**

- `building_dread_encampment`
- `building_fortress`
- `building_military_academy`
- `building_planetary_shield_generator`
- `building_stronghold`

### `common/buildings/10_deposit_buildings.txt`

Objects: **5**

- `building_betharian_power_plant`
- `building_crystal_mines`
- `building_gas_extractors`
- `building_mote_harvesters`
- `building_xeno_zoo`

### `common/buildings/11_primitive_buildings.txt`

Objects: **28**

- `building_crude_huts`
- `building_hive_crude_huts`
- `building_hive_primitive_capital`
- `building_hive_primitive_dwellings`
- `building_hive_primitive_factory`
- `building_hive_primitive_farm`
- `building_hive_primitive_mine`
- `building_hive_primitive_node`
- `building_hive_primitive_power_plant`
- `building_hive_stone_palace`
- `building_hive_urban_dwellings`
- `building_machine_primitive_node`
- `building_pre_ftl_radio_telescope`
- `building_primitive_capital`
- `building_primitive_clinic`
- `building_primitive_dwellings`
- `building_primitive_factory`
- `building_primitive_farm`
- `building_primitive_mine`
- `building_primitive_offices`
- `building_primitive_power_plant`
- `building_primitive_research`
- `building_solarpunk_gaiaseeder`
- `building_solarpunk_organic_paradise`
- `building_solarpunk_ranger_lodge`
- `building_solarpunk_sapling`
- `building_stone_palace`
- `building_urban_dwellings`

### `common/buildings/12_event_buildings.txt`

Objects: **12**

- `building_akx_worm_3`
- `building_artist_patron`
- `building_composer_sanctum`
- `building_crystal_plant_2`
- `building_eater_sanctum`
- `building_great_pyramid`
- `building_instrument_sanctum`
- `building_junkheap`
- `building_nuumismatic_shrine`
- `building_waste_reprocessing_center`
- `building_whisperers_sanctum`
- `building_zroni_equilibrator`

### `common/buildings/13_fallen_empire_buildings.txt`

Objects: **46**

- `building_affluence_center`
- `building_affluence_emporium`
- `building_ancient_control_center`
- `building_ancient_cryo_chamber`
- `building_ancient_hive_capital`
- `building_ancient_palace`
- `building_class_3_singularity`
- `building_class_4_singularity`
- `building_dimensional_fabricator`
- `building_dimensional_replicator`
- `building_empyrean_shrine`
- `building_fe_administration_1`
- `building_fe_administration_2`
- `building_fe_administration_hive_1`
- `building_fe_administration_hive_2`
- `building_fe_administration_machine_1`
- `building_fe_administration_machine_2`
- `building_fe_assembly_1`
- `building_fe_assembly_2`
- `building_fe_clinic_1`
- `building_fe_clinic_2`
- `building_fe_dome`
- `building_fe_entertainment_1`
- `building_fe_entertainment_2`
- `building_fe_fortress`
- `building_fe_lab_1`
- `building_fe_lab_2`
- `building_fe_market_1`
- `building_fe_market_2`
- `building_fe_mine_1`
- `building_fe_mine_2`
- `building_fe_security_1`
- `building_fe_security_2`
- `building_fe_silo_1`
- `building_fe_silo_2`
- `building_fe_sky_dome`
- `building_fe_stronghold`
- `building_fe_temple_1`
- `building_fe_temple_2`
- `building_fe_xeno_zoo`
- `building_hab_fe_capital`
- `building_master_archive`
- `building_micro_forge`
- `building_nano_forge`
- `building_nourishment_center`
- `building_nourishment_complex`

### `common/buildings/14_branch_office_buildings.txt`

Objects: **35**

- `building_ai_emporium`
- `building_amusement_megaplex`
- `building_augmentation_bazaars_branch`
- `building_bio_reprocessing_facilities`
- `building_carceral_test_facility`
- `building_clear_thought_clinic`
- `building_commercial_forum`
- `building_corporate_clinics`
- `building_corporate_embassy`
- `building_disinformation_center`
- `building_executive_retreat`
- `building_food_conglomerate`
- `building_illicit_research_labs`
- `building_imperial_concession_port`
- `building_industrial_subsidiary`
- `building_knightly_theme_park`
- `building_living_metal_clinic`
- `building_military_contractors`
- `building_pirate_haven`
- `building_private_mining_consortium`
- `building_private_research_initiative`
- `building_private_security`
- `building_private_shipyards`
- `building_psionic_offices`
- `building_public_relations_office`
- `building_smuggling_rings`
- `building_subversive_shrine`
- `building_syndicate_outreach_office`
- `building_temple_of_prosperity`
- `building_underground_chemists`
- `building_underground_clubs`
- `building_virtual_entertainment_studios`
- `building_wildcat_miners`
- `building_wrecking_yards`
- `building_xeno_tourism_agency`

### `common/buildings/15_overlord_holdings.txt`

Objects: **30**

- `holding_aid_agency`
- `holding_communal_housing_outreach`
- `holding_distributed_processing`
- `holding_dread_outpost`
- `holding_emporium`
- `holding_energy_requisitorium`
- `holding_experimental_crater`
- `holding_franchise_headquarters`
- `holding_garrison`
- `holding_idyllic_bloom`
- `holding_knight_commandery`
- `holding_material_requisitorium`
- `holding_noble_vacation_homes`
- `holding_offspring_nest`
- `holding_offworld_foundry`
- `holding_orbital_assembly_complex`
- `holding_organic_sanctuary`
- `holding_overlord_vigil_command`
- `holding_parasitic_algorithms`
- `holding_park_ranger_lodge`
- `holding_produce_requisitorium`
- `holding_propaganda_office`
- `holding_recruitment_office`
- `holding_reemployment_center`
- `holding_sacrificial_shrine`
- `holding_satellite_campus`
- `holding_splinter_hive`
- `holding_transcendental_retreat`
- `holding_tree_of_life_sapling`
- `holding_wilderness_glade`

### `common/buildings/16_first_contact_buildings.txt`

Objects: **6**

- `building_low_tech_admin_hub`
- `building_low_tech_capital`
- `building_low_tech_farm`
- `building_low_tech_power_plant`
- `building_low_tech_research_lab`
- `building_low_tech_scrap_refinery`

### `common/buildings/17_paragon_buildings.txt`

Objects: **3**

- `building_contained_ecosphere`
- `building_paragon_memory_vaults`
- `building_the_beholder`

### `common/buildings/18_astral_planes_buildings.txt`

Objects: **3**

- `building_astral_siphon_1`
- `building_astral_siphon_2`
- `building_astral_siphon_3`

### `common/buildings/19_cosmic_storm_buildings.txt`

Objects: **11**

- `building_adakkaria_patriotic_institute`
- `building_advanced_storm_attraction_center`
- `building_advanced_storm_repellent_center`
- `building_advanced_storm_resistant_production`
- `building_astrometeorology_observation_center`
- `building_storm_attraction_center`
- `building_storm_grand_theater`
- `building_storm_holo_theater`
- `building_storm_repellent_center`
- `building_storm_resistant_production`
- `building_storm_summoning_theater`

### `common/buildings/20_machine_age_buildings.txt`

Objects: **32**

- `building_abandoned_gene_clinic`
- `building_amphitheater_of_the_mind`
- `building_augmentation_bazaars`
- `building_augmentation_center`
- `building_battlement_of_steel`
- `building_cyberdome`
- `building_forge_of_the_fellowship`
- `building_grand_battlements_of_steel`
- `building_grand_cathedral_of_toil`
- `building_grand_concert_hall_of_the_mind`
- `building_grand_forge_of_the_fellowship`
- `building_hive_transcendental_retreat`
- `building_identity_complex`
- `building_identity_repository`
- `building_lathe_capital`
- `building_lathe_cogitator`
- `building_lathe_life_support`
- `building_lathe_major_capital`
- `building_lathe_overclocker`
- `building_lathe_preserver`
- `building_lathe_reactor`
- `building_lathe_resonator`
- `building_lathe_stabilisator`
- `building_lathe_super_capital`
- `building_lathe_validator`
- `building_nanolab_1`
- `building_nanolab_2`
- `building_nanotech_cauldron`
- `building_sanctuary_of_toil`
- `building_the_sanctum_of_augmentation`
- `building_the_united_sanctum_of_augmentation`
- `building_transcendental_retreat`

### `common/buildings/21_grand_archive_buildings.txt`

Objects: **18**

- `aesthetic_wonders_holomuseum`
- `galactic_history_holomuseum`
- `hunting_grounds`
- `hunting_grounds_2`
- `hunting_grounds_3`
- `primal_arena`
- `primal_arena_2`
- `primal_arena_3`
- `symbiosis_nexus`
- `symbiosis_nexus_2`
- `symbiosis_nexus_3`
- `wildlife_ranch`
- `wildlife_ranch_2`
- `wildlife_ranch_3`
- `wildlife_sanctuary`
- `wildlife_sanctuary_2`
- `wildlife_sanctuary_3`
- `xeno_geology_holomuseum`

### `common/buildings/21_wilderness_buildings.txt`

Objects: **46**

- `building_avatar_chamber_1`
- `building_avatar_chamber_2`
- `building_avatar_chamber_3`
- `building_avatar_chamber_4`
- `building_bioelectric_stimulator_1`
- `building_bioelectric_stimulator_2`
- `building_bioelectric_stimulator_3`
- `building_bioelectric_stimulator_4`
- `building_brain_node_1`
- `building_brain_node_2`
- `building_brain_node_3`
- `building_brain_node_4`
- `building_capital_wilderness`
- `building_churning_stomach`
- `building_churning_tunnels_1`
- `building_churning_tunnels_2`
- `building_churning_tunnels_3`
- `building_churning_tunnels_4`
- `building_colony_shelter_wilderness`
- `building_commensal_clearing_1`
- `building_commensal_clearing_2`
- `building_commensal_clearing_3`
- `building_commensal_clearing_4`
- `building_cradle_of_rebirth`
- `building_crystal_growth`
- `building_imperial_capital_wilderness`
- `building_major_capital_wilderness`
- `building_massive_growth_1`
- `building_massive_growth_2`
- `building_massive_growth_3`
- `building_massive_growth_4`
- `building_mote_aggravator`
- `building_natural_furnace_0`
- `building_natural_furnace_1`
- `building_natural_furnace_2`
- `building_natural_furnace_3`
- `building_ozone_thickener`
- `building_planetary_carapace`
- `building_planetary_carapace_2`
- `building_subterranean_cache`
- `building_system_capital_wilderness`
- `building_tendril_cradle_1`
- `building_tendril_cradle_2`
- `building_tendril_cradle_3`
- `building_tendril_cradle_4`
- `building_wilderness_storm_relief`

### `common/buildings/22_biogenesis_buildings.txt`

Objects: **2**

- `building_citadel_uplink`
- `building_genomic_facility`

### `common/buildings/22_extreme_frontiers_buildings.txt`

Objects: **3**

- `building_bio_furnace`
- `building_cryovault`
- `building_pinniped_sanctuary`

### `common/buildings/23_shroud_buildings.txt`

Objects: **21**

- `building_ancient_ward_1`
- `building_ancient_ward_2`
- `building_chamber_of_silence`
- `building_cradle_sanctum`
- `building_experimentation_chambers_1`
- `building_experimentation_chambers_2`
- `building_experimentation_chambers_3`
- `building_lifecrypt_1`
- `building_lifecrypt_2`
- `building_lifecrypt_3`
- `building_lifecrypt_corporate_1`
- `building_lifecrypt_corporate_2`
- `building_lifecrypt_corporate_3`
- `building_lifecrypt_hive_mind_1`
- `building_lifecrypt_hive_mind_2`
- `building_lifecrypt_hive_mind_3`
- `building_lifecrypt_machine_1`
- `building_lifecrypt_machine_2`
- `building_lifecrypt_machine_3`
- `building_materiality_engine`
- `building_psionic_suppressor`

## Jobs / pop_jobs

Path: `common/pop_jobs`

| Vanilla file | Objects |
|---|---:|
| `common/pop_jobs/00_other_jobs.txt` | 40 |
| `common/pop_jobs/01_ruler_jobs.txt` | 10 |
| `common/pop_jobs/02_specialist_jobs.txt` | 39 |
| `common/pop_jobs/03_worker_jobs.txt` | 17 |
| `common/pop_jobs/04_gestalt_jobs.txt` | 39 |
| `common/pop_jobs/05_primitive_jobs.txt` | 46 |
| `common/pop_jobs/06_event_jobs.txt` | 39 |
| `common/pop_jobs/07_fallen_empire_jobs.txt` | 14 |
| `common/pop_jobs/08_overlord_jobs.txt` | 42 |
| `common/pop_jobs/09_first_contact_jobs.txt` | 10 |
| `common/pop_jobs/10_paragon_fake_jobs.txt` | 13 |
| `common/pop_jobs/11_astral_planes_jobs.txt` | 7 |
| `common/pop_jobs/12_cosmic_storm_jobs.txt` | 3 |
| `common/pop_jobs/13_machine_age_jobs.txt` | 13 |
| `common/pop_jobs/14_grand_archive_jobs.txt` | 4 |
| `common/pop_jobs/15_biogenesis_jobs.txt` | 7 |
| `common/pop_jobs/15_gestalt_unemployment.txt` | 2 |
| `common/pop_jobs/15_strange_worlds_jobs.txt` | 6 |
| `common/pop_jobs/15_unemployment.txt` | 5 |
| `common/pop_jobs/16_shroud_jobs.txt` | 14 |
| `common/pop_jobs/99_swap_jobs.txt` | 3 |

### `common/pop_jobs/00_other_jobs.txt`

Objects: **40**

- `assimilation`
- `bio_trophy`
- `bio_trophy_processing`
- `bio_trophy_unprocessing`
- `civilian`
- `corrupt_drone`
- `criminal`
- `crisis_purge`
- `deviant_drone`
- `fotd_protectors`
- `heart_processing`
- `livestock`
- `livestock_infernal`
- `livestock_lithoid`
- `livestock_zoo_animal`
- `livestock_zoo_animal_lithoid`
- `livestock_zoo_beast`
- `livestock_zoo_beast_lithoid`
- `organic_battery`
- `organic_exhibit`
- `presapient_processing`
- `presapient_unprocessing`
- `purge`
- `purge_labor_camps`
- `purge_lithoid`
- `purge_matrix`
- `purge_processing`
- `purge_processing_infernal`
- `purge_processing_lithoid`
- `purge_processing_robot`
- `purge_robot`
- `purge_sacrifice`
- `purge_unprocessing`
- `robot_servant_processing`
- `robot_servant_unprocessing`
- `servant`
- `slave_overseer`
- `slave_processing`
- `slave_toiler`
- `slave_unprocessing`

### `common/pop_jobs/01_ruler_jobs.txt`

Objects: **10**

- `dystopian_enforcer`
- `dystopian_telepath`
- `executive`
- `head_researcher`
- `high_priest`
- `knight_commander`
- `merchant`
- `noble`
- `politician`
- `warden`

### `common/pop_jobs/02_specialist_jobs.txt`

Objects: **39**

- `archaeoengineers`
- `artificer`
- `artisan`
- `bath_attendant`
- `bath_attendant_individual_machine`
- `battle_thrall`
- `biologist`
- `bureaucrat`
- `catalytic_technician`
- `chemist`
- `culture_worker`
- `death_chronicler`
- `educator`
- `enforcer`
- `engineer`
- `entertainer`
- `foundry`
- `gas_refiner`
- `healthcare`
- `knight`
- `manager`
- `necro_apprentice`
- `necromancer`
- `numistic_priest`
- `offworld_prospector`
- `pearl_diver`
- `physicist`
- `polytechnic_mentor`
- `preacher`
- `reassigner`
- `resort_worker`
- `roboticist`
- `soldier`
- `steward`
- `telepath`
- `trader`
- `translucer`
- `unifier`
- `xeno_zoo_keeper`

### `common/pop_jobs/03_worker_jobs.txt`

Objects: **17**

- `angler`
- `artificer_prison_worker`
- `artisan_prison_worker`
- `catalytic_technician_prison_worker`
- `clerk`
- `colonist`
- `crystal_miner`
- `farmer`
- `foundry_prison_worker`
- `gas_extractor`
- `miner`
- `mortal_initiate`
- `mote_harvester`
- `ranger`
- `scrap_miner`
- `squire`
- `technician`

### `common/pop_jobs/04_gestalt_jobs.txt`

Objects: **39**

- `agri_drone`
- `alloy_drone`
- `archaeo_drone`
- `archaeo_unit`
- `artisan_drone`
- `bath_attendant_hive`
- `bath_attendant_machine`
- `brain_drone_biologist`
- `brain_drone_engineer`
- `brain_drone_physicist`
- `calculator_biologist`
- `calculator_engineer`
- `calculator_physicist`
- `catalytic_drone`
- `chemist_drone`
- `chronicle_drone`
- `coordinator`
- `crystal_mining_drone`
- `evaluator`
- `fabricator`
- `gas_extraction_drone`
- `gas_refiner_drone`
- `gestation_drone`
- `logistics_drone`
- `maintenance_drone`
- `mining_drone`
- `mote_harvesting_drone`
- `offspring_drone`
- `offworld_prospector_drone`
- `patrol_drone`
- `polytechnic_drone`
- `replicator`
- `scrap_miner_drone`
- `spawning_drone`
- `synapse_drone`
- `technician_drone`
- `translucer_drone`
- `warrior_drone`
- `wilderness_maintenance_drone`

### `common/pop_jobs/05_primitive_jobs.txt`

Objects: **46**

- `hive_basic_agri_drone`
- `hive_basic_agri_drone_lithoid`
- `hive_sustenance_drone`
- `hive_sustenance_drone_lithoid`
- `hunted_pre_sapient`
- `hunted_pre_sapient_lithoid`
- `hunter_gatherer`
- `hunter_gatherer_lithoid`
- `peasant`
- `peasant_lithoid`
- `pre_sapient`
- `pre_sapient_nascent`
- `primitive_administrator`
- `primitive_bureaucrat`
- `primitive_entertainer`
- `primitive_farmer`
- `primitive_hive_brain_drone`
- `primitive_hive_cerebellum_drone`
- `primitive_hive_factory_drone`
- `primitive_hive_farmer`
- `primitive_hive_miner`
- `primitive_hive_spawning_drone`
- `primitive_hive_synapse_drone`
- `primitive_hive_synapse_drone_2`
- `primitive_hive_technician`
- `primitive_hive_warrior`
- `primitive_hive_warrior_2`
- `primitive_laborer`
- `primitive_miner`
- `primitive_noble`
- `primitive_priest`
- `primitive_priest_2`
- `primitive_researcher`
- `primitive_researcher_2`
- `primitive_technician`
- `primitive_warrior`
- `primitive_warrior_2`
- `solarpunk_anarchist`
- `xeno_zoo_animal`
- `xeno_zoo_animal_lithoid`
- `xeno_zoo_animal_lithoid_nascent`
- `xeno_zoo_animal_nascent`
- `xeno_zoo_beast`
- `xeno_zoo_beast_lithoid`
- `xeno_zoo_beast_lithoid_nascent`
- `xeno_zoo_beast_nascent`

### `common/pop_jobs/06_event_jobs.txt`

Objects: **39**

- `alien_hunter`
- `archivist`
- `astrogarbage_collector`
- `astrogarbage_collector_gestalt`
- `cave_cleaner`
- `cave_cleaner_gestalt`
- `dimensional_portal_researcher`
- `dimensional_portal_researcher_gestalt`
- `event_purge`
- `gas_plant_engineer`
- `gas_plant_engineer_gestalt`
- `machine_nurse`
- `manufactorium_complex_drone`
- `manufactorium_scraper`
- `manufactorium_scraper_drone`
- `manufactorium_specialist`
- `mineral_diver`
- `mineral_diver_drone`
- `myrmeku_power_farmer`
- `myrmeku_power_farmer_gestalt`
- `odd_factory_drone`
- `odd_factory_worker`
- `puddle_technician`
- `puddle_technician_drone`
- `ratling_scavenger`
- `robot_caretaker`
- `space_time_anomaly_researcher`
- `space_time_anomaly_researcher_gestalt`
- `stasis_warden`
- `stasis_warden_drone`
- `stratovent_refiner`
- `stratovent_refiner_minerals`
- `stratovent_refiner_upg`
- `stratovent_researcher`
- `titan_hunter`
- `turtle_miner`
- `turtle_miner_gestalt`
- `underground_contact_drone`
- `underground_trade_worker`

### `common/pop_jobs/07_fallen_empire_jobs.txt`

Objects: **14**

- `fe_acolyte_artisan`
- `fe_acolyte_farm`
- `fe_acolyte_generator`
- `fe_acolyte_mine`
- `fe_archivist`
- `fe_augur`
- `fe_guardian_bot`
- `fe_hedonist`
- `fe_maintenance_bot`
- `fe_overseer`
- `fe_protector`
- `fe_sky_cardinal`
- `fe_xeno_keeper`
- `fe_xeno_ward`

### `common/pop_jobs/08_overlord_jobs.txt`

Objects: **42**

- `aid_worker`
- `aid_worker_drone`
- `mind_thrall`
- `mind_thrall_drone`
- `overlord_academic`
- `overlord_academic_drone`
- `overlord_arborist`
- `overlord_arborist_drone`
- `overlord_beholder`
- `overlord_beholder_drone`
- `overlord_bio_trophy`
- `overlord_bio_trophy_drone`
- `overlord_breeder`
- `overlord_breeder_drone`
- `overlord_catalytic_drone`
- `overlord_catalytic_technician`
- `overlord_fabricator`
- `overlord_foundry_drone`
- `overlord_healthcare`
- `overlord_knight`
- `overlord_knight_drone`
- `overlord_manager`
- `overlord_metallurgist`
- `overlord_mortal_initiate`
- `overlord_mortal_initiate_drone`
- `overlord_necromancer`
- `overlord_necromancer_drone`
- `overlord_offspring_drone_feeder`
- `overlord_offspring_drone_feeder_drone`
- `overlord_propagandist`
- `overlord_propagandist_drone`
- `overlord_ranger`
- `overlord_ranger_drone`
- `overlord_reassigner`
- `overlord_reassigner_drone`
- `overlord_recruiter`
- `overlord_recruiter_drone`
- `overlord_replicator`
- `overlord_spawning_drone`
- `overlord_spawning_drone_lithoid`
- `overlord_trader`
- `overlord_trader_drone`

### `common/pop_jobs/09_first_contact_jobs.txt`

Objects: **10**

- `broken_shackles_scavenger`
- `low_tech_bureaucrat`
- `low_tech_farmer`
- `low_tech_laborer`
- `low_tech_manager`
- `low_tech_miner`
- `low_tech_priest`
- `low_tech_researcher`
- `low_tech_technician`
- `low_tech_warrior`

### `common/pop_jobs/10_paragon_fake_jobs.txt`

Objects: **13**

- `captain`
- `chief_navigator`
- `chief_security_officer`
- `chief_supply_officer`
- `commanding_officer`
- `government_employee`
- `intelligence_officer`
- `none`
- `principal_pilot`
- `researcher`
- `ship_logistics_officer`
- `ship_weapons_officer`
- `special_operations_commander`

### `common/pop_jobs/11_astral_planes_jobs.txt`

Objects: **7**

- `astral_drone`
- `astral_researcher`
- `astral_unit`
- `munitions_decommissioner`
- `munitions_decommissioning_drone`
- `munitions_decommissioning_unit`
- `munitions_decommissioning_unit_lithoid`

### `common/pop_jobs/12_cosmic_storm_jobs.txt`

Objects: **3**

- `astrometeorologist`
- `astrometeorologist_hive`
- `astrometeorologist_machine`

### `common/pop_jobs/13_machine_age_jobs.txt`

Objects: **13**

- `augmentor`
- `augmentor_drone`
- `clip_maximizer`
- `cyberdome_duelist`
- `cyberdome_spectator`
- `haruspex`
- `identity_designer`
- `nanotech_research_unit`
- `nanotech_researcher`
- `neural_chip`
- `neural_chip_processing`
- `neural_chip_unprocessing`
- `technophant`

### `common/pop_jobs/14_grand_archive_jobs.txt`

Objects: **4**

- `drone_wrangler`
- `treasure_gatherer`
- `treasure_gatherer_gestalt`
- `wrangler`

### `common/pop_jobs/15_biogenesis_jobs.txt`

Objects: **7**

- `disconnected_drone`
- `genomic_drone`
- `genomic_researcher`
- `skywatcher`
- `skywatcher_drone`
- `transference_drone`
- `transference_volunteer`

### `common/pop_jobs/15_gestalt_unemployment.txt`

Objects: **2**

- `complex_drone_unemployment`
- `simple_drone_unemployment`

### `common/pop_jobs/15_strange_worlds_jobs.txt`

Objects: **6**

- `drone_sand_caretaker`
- `drone_sand_whisperer`
- `drone_space_junk_collector`
- `sand_caretaker`
- `sand_whisperer`
- `space_junk_collector`

### `common/pop_jobs/15_unemployment.txt`

Objects: **5**

- `bio_trophy_unemployment`
- `ruler_unemployment`
- `slave_unemployment`
- `specialist_unemployment`
- `worker_unemployment`

### `common/pop_jobs/16_shroud_jobs.txt`

Objects: **14**

- `drone_energy_thrall`
- `energy_thrall`
- `experiment_engineer`
- `experiment_engineer_drone`
- `extradimensional_research_unit`
- `observator_drone`
- `physician_drone`
- `production_overseer`
- `shroud_trader`
- `slave_orderly`
- `spe_colonist`
- `telepath_drone`
- `test_subject`
- `test_subject_drone`

### `common/pop_jobs/99_swap_jobs.txt`

Objects: **3**

- `duelist`
- `historical_curator`
- `storm_dancer`
