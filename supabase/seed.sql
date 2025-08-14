-- QuantumMateria Story Engine - Comprehensive Seed Data
-- Fantasy Adventure: "The Crown of Starlight"
-- A tale of Lyra Dawnweaver's quest to retrieve the Crown of Starlight and save the realm

-- Clear existing data
TRUNCATE TABLE dag_edges, timeline_events, knowledge_snapshots, relationships, story_goals, milestones, scene_blocks, scenes, entities RESTART IDENTITY CASCADE;

-- =============================
-- ENTITIES
-- =============================

-- CHARACTERS
INSERT INTO entities (id, name, entity_type, description, metadata) VALUES
('11111111-1111-1111-1111-111111111111', 'Lyra Dawnweaver', 'character', 'A young mage with silver hair and piercing blue eyes. Orphaned at birth and raised by the Circle of Mages, she possesses unusual control over light magic but struggles with her mysterious past.', 
 '{"age": 23, "class": "mage", "alignment": "neutral good", "hair": "silver", "eyes": "blue", "background": "orphan", "magic_school": "light", "personality": ["curious", "determined", "empathetic"], "fears": ["abandonment", "losing control"], "goals": ["discover her heritage", "master her powers"]}'),

('22222222-2222-2222-2222-222222222222', 'Kael Shadowbane', 'character', 'A fallen paladin turned mercenary. Once a champion of light, he was corrupted by dark magic while trying to save his village. Now he seeks redemption while wrestling with inner darkness.', 
 '{"age": 32, "class": "fallen paladin", "alignment": "chaotic neutral", "hair": "black with silver streaks", "eyes": "grey", "background": "noble", "corruption": "shadow magic", "personality": ["brooding", "protective", "guilt-ridden"], "skills": ["swordsmanship", "tactical combat"], "weakness": "dark magic vulnerability"}'),

('33333333-3333-3333-3333-333333333333', 'Finn Quickfingers', 'character', 'A halfling rogue with a heart of gold and fingers of quicksilver. Born into poverty, he learned to survive on the streets but maintains an optimistic outlook and fierce loyalty to friends.', 
 '{"age": 28, "class": "rogue", "alignment": "chaotic good", "height": "3ft 2in", "hair": "curly brown", "eyes": "green", "background": "street orphan", "personality": ["optimistic", "loyal", "witty"], "skills": ["lockpicking", "stealth", "acrobatics"], "loves": "good food and friends"}'),

('44444444-4444-4444-4444-444444444444', 'Magister Aldric Starfall', 'character', 'An ancient wizard and keeper of the Great Library. Over 200 years old, he has witnessed the rise and fall of kingdoms. Wise but sometimes cryptic, he guides heroes from the shadows.', 
 '{"age": 247, "class": "archmage", "alignment": "lawful neutral", "hair": "long white beard", "eyes": "deep amber", "background": "scholar", "specialization": "ancient lore", "personality": ["wise", "patient", "mysterious"], "knowledge": ["forbidden magic", "ancient history", "prophecies"]}'),

('55555555-5555-5555-5555-555555555555', 'Lord Varian Blackthorn', 'character', 'The primary antagonist. Once a noble lord, he was consumed by envy and dark ambition. He seeks the Crown of Starlight to rule all realms, believing himself the rightful heir to ultimate power.', 
 '{"age": 45, "class": "dark sorcerer", "alignment": "lawful evil", "hair": "black", "eyes": "red", "background": "noble", "corruption": "necromancy", "personality": ["ambitious", "calculating", "ruthless"], "goals": ["absolute power", "eternal rule"], "weakness": "pride and arrogance"}'),

('66666666-6666-6666-6666-666666666666', 'Sera Moonwhisper', 'character', 'An elven ranger and druid who protects the ancient forests. She becomes an unlikely ally to Lyra, sharing knowledge of nature magic and ancient forest lore.', 
 '{"age": 156, "class": "ranger/druid", "alignment": "neutral good", "hair": "silver-green", "eyes": "forest green", "background": "forest guardian", "specialization": "nature magic", "personality": ["calm", "wise", "protective"], "animal_companion": "silver wolf named Whisper"}');

-- LOCATIONS
INSERT INTO entities (id, name, entity_type, description, metadata) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'The Prancing Pony Tavern', 'location', 'A warm, bustling tavern in the heart of Millbrook village. Known for its excellent ale and as a gathering place for travelers and adventurers. The common room features a large fireplace and wooden tables worn smooth by countless patrons.', 
 '{"type": "tavern", "village": "Millbrook", "atmosphere": "warm and welcoming", "specialties": ["honey mead", "roasted mutton", "travelers tales"], "proprietor": "Bren Goldenbrew", "rooms": 12, "capacity": 50}'),

('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Whispering Woods', 'location', 'An ancient enchanted forest where magic still flows freely. The trees here are older than memory, and strange lights dance between their branches at night. Home to elves, fey creatures, and ancient secrets.', 
 '{"type": "ancient forest", "magic_level": "high", "inhabitants": ["elves", "fey", "treants"], "dangers": ["dark creatures", "illusions", "getting lost"], "magical_properties": ["enhanced spellcasting", "time distortion"], "sacred_groves": 3}'),

('cccccccc-cccc-cccc-cccc-cccccccccccc', 'The Great Library of Aethermoor', 'location', 'A massive repository of knowledge built into a living mountain. Contains scrolls and books from across all realms, including forbidden texts and prophecies. Protected by powerful wards and magical guardians.', 
 '{"type": "magical library", "floors": 37, "books": "over 100000", "sections": ["common knowledge", "arcane studies", "forbidden texts", "prophecies"], "guardians": ["stone golems", "spell wards"], "access": "invitation only"}'),

('dddddddd-dddd-dddd-dddd-dddddddddddd', 'Shadowmere Castle', 'location', 'Lord Blackthorn''s imposing fortress, built from black stone and shrouded in perpetual shadow. The castle sits atop a craggy mountain, surrounded by storms and dark magic. Its towers pierce the sky like accusations.', 
 '{"type": "dark fortress", "stone": "obsidian", "defenses": ["shadow magic", "undead guards", "storm barriers"], "towers": 7, "dungeons": "extensive", "atmosphere": "perpetually dark", "ruler": "Lord Varian Blackthorn"}'),

('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'The Starlight Sanctum', 'location', 'A hidden temple deep within the Whispering Woods, built around a natural crystal formation that channels starlight. This is where the Crown of Starlight was originally forged and where it must be returned.', 
 '{"type": "ancient temple", "material": "living crystal", "power_source": "starlight", "access": "hidden paths", "guardians": ["celestial beings", "light spirits"], "significance": "creation site of Crown of Starlight", "alignment": "good"}');

-- ARTIFACTS
INSERT INTO entities (id, name, entity_type, description, metadata) VALUES
('ffffffff-ffff-ffff-ffff-ffffffffffff', 'Crown of Starlight', 'artifact', 'An ancient crown forged from crystallized starlight and silver from the first moon. It grants its bearer control over light and shadow, the ability to see truth, and protection from dark magic. Currently missing, stolen by Lord Blackthorn.', 
 '{"type": "legendary crown", "material": ["crystallized starlight", "lunar silver"], "powers": ["light control", "truth sight", "shadow manipulation", "dark magic immunity"], "origin": "Starlight Sanctum", "creator": "the First Mages", "status": "stolen", "current_holder": "Lord Varian Blackthorn"}'),

('9a9a9a9a-9a9a-9a9a-9a9a-9a9a9a9a9a9a', 'Moonblade', 'artifact', 'Kael''s ancestral sword, blessed by lunar magic. The blade glows with silver light and can cut through dark magic. It was given to his family line by ancient moon priests and chooses its own wielder.', 
 '{"type": "magical sword", "material": ["moon steel", "silver"], "enchantments": ["silver light", "dark magic cutting", "self-selecting"], "origin": "moon priests", "family": "Shadowbane lineage", "sentience": "semi-aware", "alignment": "lawful good"}'),

('9b9b9b9b-9b9b-9b9b-9b9b-9b9b9b9b9b9b', 'Lockpick of Opening', 'artifact', 'Finn''s prized possession - a master lockpick that can open any non-magical lock and even some magical ones. Made from a fragment of the first key ever forged, it seems to understand the nature of all locks.', 
 '{"type": "magical tool", "material": "first-key fragment", "abilities": ["open any lock", "sense traps", "magical lock detection"], "origin": "unknown thief master", "rarity": "unique", "size": "palm-sized", "intelligence": "basic"}'),

('9c9c9c9c-9c9c-9c9c-9c9c-9c9c9c9c9c9c', 'Tome of Whispered Secrets', 'artifact', 'A leather-bound grimoire containing dangerous knowledge of shadow magic and forbidden spells. Found in Blackthorn''s possession, it corrupts those who read it but grants immense power. Contains the ritual to bind the Crown.', 
 '{"type": "cursed grimoire", "material": ["shadow-touched leather", "blood ink"], "contents": ["shadow spells", "binding rituals", "forbidden knowledge"], "corruption_level": "high", "power_level": "immense", "warning": "corrupts readers", "pages": 333}');

-- EVENTS
INSERT INTO entities (id, name, entity_type, description, metadata) VALUES
('9d9d9d9d-9d9d-9d9d-9d9d-9d9d9d9d9d9d', 'The Great Theft', 'event', 'The night Lord Blackthorn infiltrated the Starlight Sanctum and stole the Crown of Starlight, breaking ancient wards and killing several guardians. This event plunged the realm into growing darkness.', 
 '{"type": "major theft", "perpetrator": "Lord Varian Blackthorn", "target": "Crown of Starlight", "location": "Starlight Sanctum", "casualties": 7, "consequences": ["growing darkness", "weakened light magic", "imbalance"], "witness": "surviving guardian"}'),

('9e9e9e9e-9e9e-9e9e-9e9e-9e9e9e9e9e9e', 'The Corruption of Kael', 'event', 'The tragic day when Kael attempted to save his village from a shadow plague but was overwhelmed by dark magic, leading to his corruption and fall from grace as a paladin.', 
 '{"type": "corruption event", "victim": "Kael Shadowbane", "cause": "shadow plague", "location": "Millhaven Village", "attempt": "heroic rescue", "result": "corruption", "lost": ["paladin status", "divine connection"], "gained": ["shadow magic", "guilt"]}'),

('9f9f9f9f-9f9f-9f9f-9f9f-9f9f9f9f9f9f', 'The Prophecy Revealed', 'event', 'Magister Aldric reveals an ancient prophecy that speaks of a silver-haired mage who will either save the realm or destroy it, depending on the choices made when darkness threatens to consume all.', 
 '{"type": "prophecy revelation", "revealer": "Magister Aldric Starfall", "subject": "Lyra Dawnweaver", "content": "silver-haired savior or destroyer", "conditions": "choices during darkness", "significance": "realm''s fate", "ancient_origin": true}');

-- KNOWLEDGE FACTS
INSERT INTO entities (id, name, entity_type, description, metadata) VALUES
('8a8a8a8a-8a8a-8a8a-8a8a-8a8a8a8a8a8a', 'The Crown''s True Purpose', 'knowledge_fact', 'The Crown of Starlight was not created to rule, but to maintain the balance between light and shadow in the world. It chooses its bearer based on their heart, not their power or birthright.', 
 '{"type": "ancient secret", "subject": "Crown of Starlight", "truth": "balance maintenance tool", "selection_criteria": "pure heart", "misconception": "ruling artifact", "known_by": ["Magister Aldric", "ancient guardians"], "importance": "critical"}'),

('8b8b8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b', 'Lyra''s Hidden Heritage', 'knowledge_fact', 'Lyra is the last descendant of the First Mages who created the Crown. Her silver hair and natural light magic are signs of her bloodline, making her the Crown''s rightful guardian.', 
 '{"type": "bloodline secret", "subject": "Lyra Dawnweaver", "heritage": "First Mages descendant", "signs": ["silver hair", "light magic affinity"], "role": "rightful guardian", "hidden_from": "Lyra herself", "known_by": ["Magister Aldric"], "revelation_timing": "crucial moment"}'),

('8c8c8c8c-8c8c-8c8c-8c8c-8c8c8c8c8c8c', 'The Shadow Plague''s Origin', 'knowledge_fact', 'The shadow plague that corrupted Kael was the first manifestation of the realm''s imbalance after the Crown was stolen. Blackthorn''s theft created a cascade of dark magic that spreads like disease.', 
 '{"type": "causal secret", "subject": "shadow plague", "origin": "Crown theft aftermath", "perpetrator": "Lord Blackthorn", "nature": "magical imbalance", "spread": "disease-like", "cure": "restore Crown", "known_by": ["few scholars"], "victims": "increasing"}');

-- =============================
-- SCENES
-- =============================

INSERT INTO scenes (id, title, location_id, timestamp) VALUES
('1a111111-1111-1111-1111-111111111111', 'The Tavern Meeting', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1000),
('2a222222-2222-2222-2222-222222222222', 'The Quest Begins', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1500),
('3a333333-3333-3333-3333-333333333333', 'Into the Whispering Woods', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 2000),
('4a444444-4444-4444-4444-444444444444', 'The Library of Secrets', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 3000),
('5a555555-5555-5555-5555-555555555555', 'Confronting the Past', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 4000),
('6a666666-6666-6666-6666-666666666666', 'The Starlight Sanctum', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 5000),
('7a777777-7777-7777-7777-777777777777', 'Assault on Shadowmere', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 6000),
('8a888888-8888-8888-8888-888888888888', 'The Crown''s Choice', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 7000),
('9a999999-9999-9999-9999-999999999999', 'Dawn of New Balance', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 8000);

-- =============================
-- SCENE BLOCKS
-- =============================

-- Scene 1: The Tavern Meeting
INSERT INTO scene_blocks (id, scene_id, block_type, "order", content, weight, metadata) VALUES
('1b111111-1111-1111-1111-111111111111', '1a111111-1111-1111-1111-111111111111', 'prose', 1, 
'The Prancing Pony tavern buzzed with the warm chatter of evening patrons. Firelight danced across worn wooden tables where merchants counted coins and travelers shared tales of distant roads. The sweet aroma of honey mead mixed with the hearty scent of roasted mutton, creating an atmosphere of comfort that made even the weariest souls feel welcome.',
1.0, '{"mood": "welcoming", "time": "evening", "atmosphere": "busy"}'),

('1b111112-1111-1111-1111-111111111111', '1a111111-1111-1111-1111-111111111111', 'dialogue', 2, 
NULL, 1.0, '{"participants": ["Lyra", "Kael"], "mood": "tense"}');

INSERT INTO scene_blocks (id, scene_id, block_type, "order", summary, lines, weight, metadata) VALUES
('1b111113-1111-1111-1111-111111111111', '1a111111-1111-1111-1111-111111111111', 'dialogue', 3,
'Lyra approaches the mysterious stranger in dark armor', 
'[
  {"speaker": "Lyra Dawnweaver", "text": "You''re him, aren''t you? The fallen paladin everyone whispers about.", "emotion": "curious"},
  {"speaker": "Kael Shadowbane", "text": "Depends who''s asking. Though I''d hardly call myself fallen... more like redirected.", "emotion": "guarded"},
  {"speaker": "Lyra Dawnweaver", "text": "I need someone who knows the dark roads. Someone who''s walked them and survived.", "emotion": "determined"},
  {"speaker": "Kael Shadowbane", "text": "And what makes you think I''d help a mage? Your kind aren''t exactly popular with my... condition.", "emotion": "bitter"}
]'::jsonb, 1.5, '{"tension": "high", "recruitment": true}');

-- Add milestone for first meeting
INSERT INTO scene_blocks (id, scene_id, block_type, "order", subject_id, verb, object_id, weight, metadata) VALUES
('1b111114-1111-1111-1111-111111111111', '1a111111-1111-1111-1111-111111111111', 'milestone', 4, 
'11111111-1111-1111-1111-111111111111', 'meets', '22222222-2222-2222-2222-222222222222', 2.0, 
'{"significance": "party formation", "relationship_change": "strangers to allies"}');

-- Scene 2: The Quest Begins
INSERT INTO scene_blocks (id, scene_id, block_type, "order", content, weight, metadata) VALUES
('1b222221-2222-2222-2222-222222222222', '2a222222-2222-2222-2222-222222222222', 'prose', 1,
'Dawn broke over Millbrook as the unlikely trio prepared to depart. Lyra checked her spell components one final time, her silver hair catching the morning light like spun moonbeams. Kael adjusted his dark armor, the weight of his cursed sword a familiar burden at his side. Finn bounced on his toes, his pack jingling with the tools of his trade.',
1.0, '{"time": "dawn", "mood": "departure", "party_formation": true}');

INSERT INTO scene_blocks (id, scene_id, block_type, "order", summary, lines, weight, metadata) VALUES
('1b222222-2222-2222-2222-222222222222', '2a222222-2222-2222-2222-222222222222', 'dialogue', 2,
'The party discusses their destination and the dangers ahead',
'[
  {"speaker": "Finn Quickfingers", "text": "So we''re really doing this? Walking into the Whispering Woods where people go in but don''t come out?", "emotion": "nervous_excitement"},
  {"speaker": "Lyra Dawnweaver", "text": "The Great Library is our only hope of finding information about the Crown''s location. Magister Aldric will have answers.", "emotion": "resolute"},
  {"speaker": "Kael Shadowbane", "text": "The woods don''t scare me. It''s what we might find at the end of this quest that worries me.", "emotion": "ominous"},
  {"speaker": "Finn Quickfingers", "text": "Well, at least we''re all equally doomed together! I find that oddly comforting.", "emotion": "optimistic_humor"}
]'::jsonb, 1.0, '{"topic": "journey planning", "foreshadowing": true}');

-- Add milestone for quest beginning
INSERT INTO scene_blocks (id, scene_id, block_type, "order", subject_id, verb, object_id, weight, metadata) VALUES
('1b222223-2222-2222-2222-222222222222', '2a222222-2222-2222-2222-222222222222', 'milestone', 3,
'11111111-1111-1111-1111-111111111111', 'begins quest for', 'ffffffff-ffff-ffff-ffff-ffffffffffff', 3.0,
'{"significance": "main quest start", "party": ["Lyra", "Kael", "Finn"]}');

-- Scene 3: Into the Whispering Woods  
INSERT INTO scene_blocks (id, scene_id, block_type, "order", content, weight, metadata) VALUES
('1b333331-3333-3333-3333-333333333333', '3a333333-3333-3333-3333-333333333333', 'prose', 1,
'The Whispering Woods lived up to their name. Ancient trees towered overhead, their canopy so thick that noon felt like twilight. Strange lights flickered between the branches—not quite fireflies, not quite stars. The very air hummed with magic, making Lyra''s skin tingle and causing Kael''s corrupted nature to stir uneasily.',
1.5, '{"magic_level": "high", "atmosphere": "mysterious", "effects": "magical sensitivity"}');

-- Sera introduction dialogue
INSERT INTO scene_blocks (id, scene_id, block_type, "order", summary, lines, weight, metadata) VALUES
('1b333332-3333-3333-3333-333333333333', '3a333333-3333-3333-3333-333333333333', 'dialogue', 2,
'The party encounters Sera Moonwhisper, who tests their intentions',
'[
  {"speaker": "Sera Moonwhisper", "text": "Three souls walk the ancient paths. One seeks knowledge, one seeks redemption, one seeks adventure. But what do you truly seek in these sacred woods?", "emotion": "mystical_challenge"},
  {"speaker": "Lyra Dawnweaver", "text": "We seek the Great Library. The realm is in danger, and we need knowledge to save it.", "emotion": "honest_urgency"},
  {"speaker": "Sera Moonwhisper", "text": "The corruption spreads from the stolen light. Yes, I sense it in you, shadow-touched one. Yet your heart still fights the darkness.", "emotion": "perceptive_compassion"},
  {"speaker": "Kael Shadowbane", "text": "I''m not here to be judged by forest spirits.", "emotion": "defensive"},
  {"speaker": "Sera Moonwhisper", "text": "Judge? No. Guide? Perhaps. These woods test all who enter. But you... you may pass, for your cause is just.", "emotion": "accepting_wisdom"}
]'::jsonb, 2.0, '{"encounter_type": "ally_recruitment", "test": "moral_character"}');

-- Milestone: gaining forest guide
INSERT INTO scene_blocks (id, scene_id, block_type, "order", subject_id, verb, object_id, weight, metadata) VALUES
('1b333333-3333-3333-3333-333333333333', '3a333333-3333-3333-3333-333333333333', 'milestone', 3,
'66666666-6666-6666-6666-666666666666', 'joins', '11111111-1111-1111-1111-111111111111', 2.0,
'{"significance": "ally gained", "party_expansion": true, "local_knowledge": true}');

-- Scene 4: The Library of Secrets
INSERT INTO scene_blocks (id, scene_id, block_type, "order", content, weight, metadata) VALUES
('1b444441-4444-4444-4444-444444444444', '4a444444-4444-4444-4444-444444444444', 'prose', 1,
'The Great Library of Aethermoor rose before them like a mountain of knowledge. Crystalline walls pulsed with inner light, and floating books drifted between towering shelves that seemed to stretch into infinity. The very air hummed with accumulated wisdom of millennia.',
1.0, '{"atmosphere": "awe_inspiring", "magic_type": "knowledge", "scale": "massive"}');

-- Aldric reveals the prophecy
INSERT INTO scene_blocks (id, scene_id, block_type, "order", summary, lines, weight, metadata) VALUES
('1b444442-4444-4444-4444-444444444444', '4a444444-4444-4444-4444-444444444444', 'dialogue', 2,
'Magister Aldric reveals crucial information about Lyra''s heritage and the Crown',
'[
  {"speaker": "Magister Aldric Starfall", "text": "Ah, Lyra Dawnweaver. I have been expecting you, though you know not why you are truly here.", "emotion": "mysterious_knowing"},
  {"speaker": "Lyra Dawnweaver", "text": "We need to know where Lord Blackthorn has taken the Crown of Starlight. The realm grows darker each day.", "emotion": "urgent_plea"},
  {"speaker": "Magister Aldric Starfall", "text": "The Crown''s location matters less than its nature. Tell me, child, what do you know of your parentage?", "emotion": "probing_gentle"},
  {"speaker": "Lyra Dawnweaver", "text": "I... I''m an orphan. The Circle raised me. Why does this matter?", "emotion": "confused_defensive"},
  {"speaker": "Magister Aldric Starfall", "text": "Because you are the last daughter of the First Mages. The Crown does not merely seek a wielder—it seeks its guardian home.", "emotion": "revelation_profound"}
]'::jsonb, 3.0, '{"revelation": "heritage", "prophecy": true, "turning_point": true}');

-- Milestone: learning true heritage
INSERT INTO scene_blocks (id, scene_id, block_type, "order", subject_id, verb, object_id, weight, metadata) VALUES
('1b444443-4444-4444-4444-444444444444', '4a444444-4444-4444-4444-444444444444', 'milestone', 3,
'11111111-1111-1111-1111-111111111111', 'discovers', '8b8b8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b', 4.0,
'{"significance": "major revelation", "identity_change": true, "destiny_revealed": true}');

-- Continue with more scenes...
-- Scene 5: Confronting the Past
INSERT INTO scene_blocks (id, scene_id, block_type, "order", content, weight, metadata) VALUES
('1b555551-5555-5555-5555-555555555555', '5a555555-5555-5555-5555-555555555555', 'prose', 1,
'Deep in the heart of the Whispering Woods, the party made camp as the weight of Aldric''s revelation settled upon them. Lyra sat apart from the others, staring into the dancing flames as if they might reveal more secrets about her heritage.',
1.0, '{"time": "night", "mood": "contemplative", "setting": "forest camp"}');

INSERT INTO scene_blocks (id, scene_id, block_type, "order", summary, lines, weight, metadata) VALUES
('1b555552-5555-5555-5555-555555555555', '5a555555-5555-5555-5555-555555555555', 'dialogue', 2,
'Kael shares his own burden and offers comfort to Lyra',
'[
  {"speaker": "Kael Shadowbane", "text": "Learning who you really are can be a curse as much as a blessing. Trust me, I know.", "emotion": "empathetic_understanding"},
  {"speaker": "Lyra Dawnweaver", "text": "How do I live up to something like that? The First Mages created the Crown. They saved the world.", "emotion": "overwhelmed_doubt"},
  {"speaker": "Kael Shadowbane", "text": "You don''t have to be them. You just have to be you. The Crown will respond to your heart, not your bloodline.", "emotion": "encouraging_wise"},
  {"speaker": "Lyra Dawnweaver", "text": "What if my heart isn''t pure enough? What if I''m not strong enough?", "emotion": "vulnerable_fear"},
  {"speaker": "Kael Shadowbane", "text": "Then you''ll have us. Nobody faces their destiny alone, not if they''re smart.", "emotion": "protective_commitment"}
]'::jsonb, 2.0, '{"character_development": true, "bond_strengthening": true, "encouragement": true}');

-- Milestone: emotional bond formed
INSERT INTO scene_blocks (id, scene_id, block_type, "order", subject_id, verb, object_id, weight, metadata) VALUES
('1b555553-5555-5555-5555-555555555555', '5a555555-5555-5555-5555-555555555555', 'milestone', 3,
'22222222-2222-2222-2222-222222222222', 'supports', '11111111-1111-1111-1111-111111111111', 2.5,
'{"significance": "relationship deepening", "emotional_support": true, "trust_building": true}');

-- =============================
-- MILESTONES (Explicit table)
-- =============================

INSERT INTO milestones (id, scene_id, subject_id, verb, object_id, description, weight, metadata) VALUES
('10111111-1111-1111-1111-111111111111', '1a111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'recruits', '22222222-2222-2222-2222-222222222222', 'Lyra successfully recruits the fallen paladin Kael to her cause', 2.0, '{"party_formation": true}'),
('10222222-2222-2222-2222-222222222222', '2a222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'begins quest for', 'ffffffff-ffff-ffff-ffff-ffffffffffff', 'The quest to retrieve the Crown of Starlight officially begins', 3.0, '{"main_quest": true}'),
('10333333-3333-3333-3333-333333333333', '3a333333-3333-3333-3333-333333333333', '66666666-6666-6666-6666-666666666666', 'guides', '11111111-1111-1111-1111-111111111111', 'Sera offers to guide the party through the dangerous woods', 2.0, '{"ally_gained": true}'),
('10444444-4444-4444-4444-444444444444', '4a444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', 'learns about', '8b8b8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b', 'Lyra discovers her true heritage as descendant of the First Mages', 4.0, '{"major_revelation": true}'),
('10555555-5555-5555-5555-555555555555', '5a555555-5555-5555-5555-555555555555', '22222222-2222-2222-2222-222222222222', 'vows to protect', '11111111-1111-1111-1111-111111111111', 'Kael pledges to stand by Lyra regardless of the dangers ahead', 2.5, '{"loyalty_declared": true}');

-- =============================
-- RELATIONSHIPS
-- =============================

-- Evolving friendships and alliances
INSERT INTO relationships (id, source_id, target_id, relation_type, weight, starts_at, ends_at, metadata) VALUES
-- Lyra and Kael: strangers to close allies
('14111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'ally', 0.3, 1000, 2000, '{"initial_trust": "low", "status": "recruited"}'),
('14111112-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'ally', 0.7, 2000, 4000, '{"trust_building": true, "shared_danger": true}'),
('14111113-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'close_ally', 0.9, 4000, NULL, '{"deep_trust": true, "emotional_bond": true}'),

-- Lyra and Finn: friendship
('14222221-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', 'friend', 0.8, 1500, NULL, '{"easy_friendship": true, "mutual_respect": true}'),

-- Lyra and Sera: mentor/guide relationship
('14333331-3333-3333-3333-333333333333', '66666666-6666-6666-6666-666666666666', '11111111-1111-1111-1111-111111111111', 'mentor', 0.7, 2000, NULL, '{"nature_magic_guidance": true, "forest_wisdom": true}'),

-- Lyra and Aldric: student/teacher
('14444441-4444-4444-4444-444444444444', '44444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', 'mentor', 0.8, 3000, NULL, '{"knowledge_sharing": true, "heritage_revelation": true}'),

-- Antagonistic relationships
('14555551-5555-5555-5555-555555555555', '55555555-5555-5555-5555-555555555555', '11111111-1111-1111-1111-111111111111', 'enemy', 0.9, 1000, NULL, '{"primary_antagonist": true, "crown_theft": true}'),
('14555552-5555-5555-5555-555555555555', '55555555-5555-5555-5555-555555555555', '22222222-2222-2222-2222-222222222222', 'enemy', 0.7, 1000, NULL, '{"corruption_source": true, "former_paladin_hatred": true}'),

-- Kael's relationship with his corruption
('14666661-6666-6666-6666-666666666666', '22222222-2222-2222-2222-222222222222', '9e9e9e9e-9e9e-9e9e-9e9e-9e9e9e9e9e9e', 'afflicted_by', 0.8, 500, NULL, '{"shadow_corruption": true, "ongoing_struggle": true}');

-- =============================
-- KNOWLEDGE SNAPSHOTS
-- =============================

-- Lyra's evolving knowledge
INSERT INTO knowledge_snapshots (id, entity_id, timestamp, knowledge, metadata) VALUES
('1c111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 1000, 
'{"heritage": "unknown", "crown_knowledge": "basic legend", "mission": "find Crown to save realm", "allies": [], "magic_ability": "moderate light magic"}', 
'{"knowledge_level": "novice", "ignorance": ["true heritage", "crown purpose"]}'),

('1c111112-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 3000,
'{"heritage": "descendant of First Mages", "crown_knowledge": "guardian artifact, not ruling tool", "mission": "return Crown to Sanctum", "allies": ["Kael", "Finn", "Sera"], "magic_ability": "growing light magic", "destiny": "Crown guardian"}',
'{"knowledge_level": "enlightened", "major_revelation": "heritage discovered"}'),

-- Kael's knowledge evolution  
('1c222221-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 1000,
'{"corruption": "shadow magic in blood", "past": "failed to save village", "guilt": "overwhelming", "purpose": "seeking redemption", "abilities": ["corrupted paladin powers", "shadow resistance"]}',
'{"emotional_state": "guilt-ridden", "motivation": "redemption"}'),

('1c222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 4000,
'{"corruption": "manageable with purpose", "past": "accepted failure, focused on present", "guilt": "lessened", "purpose": "protect Lyra and complete quest", "abilities": ["controlled shadow powers", "enhanced combat"], "revelation": "corruption can be strength when properly channeled"}',
'{"emotional_state": "determined", "character_growth": "significant"}'),

-- Finn's knowledge (consistent optimist)
('1c333331-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 1000,
'{"background": "street orphan", "skills": ["lockpicking", "stealth", "survival"], "philosophy": "stay positive", "loyalty": "to friends", "fears": ["losing companions"]}',
'{"personality": "optimistic", "role": "comic relief and skills"}'),

-- Sera's ancient knowledge
('1c666661-6666-6666-6666-666666666666', '66666666-6666-6666-6666-666666666666', 2000,
'{"forest_lore": "comprehensive", "magic_knowledge": "nature and balance", "crown_history": "knows creation story", "corruption_understanding": "sees shadow plague spreading", "duty": "protect natural balance"}',
'{"wisdom_level": "ancient", "role": "guide and protector"}'),

-- Aldric's vast knowledge
('1c444441-4444-4444-4444-444444444444', '44444444-4444-4444-4444-444444444444', 3000,
'{"prophecies": "complete knowledge", "crown_secrets": "full understanding of purpose", "bloodlines": "knows all magical lineages", "current_crisis": "understands full scope", "role": "guide destiny without controlling it"}',
'{"wisdom_level": "master", "responsibility": "guide without interference"}'),

-- Blackthorn's knowledge
('1c555551-5555-5555-5555-555555555555', '55555555-5555-5555-5555-555555555555', 1000,
'{"crown_power": "believes it grants absolute rule", "corruption_magic": "master of shadow arts", "prophecy": "aware but misinterprets", "weakness": "pride blinds him to crown true nature", "plan": "use Crown to dominate all realms"}',
'{"knowledge_level": "expert but flawed", "fatal_flaw": "misunderstands Crown purpose"}');

-- =============================
-- TIMELINE EVENTS
-- =============================

INSERT INTO timeline_events (id, scene_id, entity_id, timestamp, summary, metadata) VALUES
('17111111-1111-1111-1111-111111111111', '1a111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 1000, 'Lyra begins her quest by recruiting unlikely allies at the Prancing Pony', '{"event_type": "quest_start"}'),
('17222222-2222-2222-2222-222222222222', '3a333333-3333-3333-3333-333333333333', '66666666-6666-6666-6666-666666666666', 2000, 'Sera joins the party as guide through the Whispering Woods', '{"event_type": "ally_join"}'),
('17333333-3333-3333-3333-333333333333', '4a444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', 3000, 'Lyra discovers her true heritage as descendant of the First Mages', '{"event_type": "major_revelation"}'),
('17444444-4444-4444-4444-444444444444', '5a555555-5555-5555-5555-555555555555', '22222222-2222-2222-2222-222222222222', 4000, 'Kael pledges unwavering loyalty to Lyra and the quest', '{"event_type": "loyalty_declaration"}'),
('17555555-5555-5555-5555-555555555555', NULL, '55555555-5555-5555-5555-555555555555', 500, 'Lord Blackthorn steals the Crown of Starlight from the Sanctum', '{"event_type": "inciting_incident", "referenced_event": true}'),
('17666666-6666-6666-6666-666666666666', NULL, '22222222-2222-2222-2222-222222222222', 200, 'Kael becomes corrupted while trying to save his village from shadow plague', '{"event_type": "character_corruption", "referenced_event": true}');

-- =============================
-- STORY GOALS
-- =============================

INSERT INTO story_goals (id, description, subject_id, verb, object_id, milestone_id) VALUES
('19111111-1111-1111-1111-111111111111', 'Retrieve the Crown of Starlight from Lord Blackthorn', '11111111-1111-1111-1111-111111111111', 'retrieves', 'ffffffff-ffff-ffff-ffff-ffffffffffff', NULL),
('19222222-2222-2222-2222-222222222222', 'Restore balance between light and shadow to the realm', '11111111-1111-1111-1111-111111111111', 'restores', NULL, NULL),
('19333333-3333-3333-3333-333333333333', 'Defeat Lord Blackthorn and end his dark reign', '11111111-1111-1111-1111-111111111111', 'defeats', '55555555-5555-5555-5555-555555555555', NULL),
('19444444-4444-4444-4444-444444444444', 'Find redemption for past failures', '22222222-2222-2222-2222-222222222222', 'achieves', NULL, NULL),
('19555555-5555-5555-5555-555555555555', 'Protect friends and prove loyalty matters more than blood', '33333333-3333-3333-3333-333333333333', 'protects', '11111111-1111-1111-1111-111111111111', NULL);

-- =============================
-- DAG EDGES (Causal Relationships)
-- =============================

INSERT INTO dag_edges (id, from_id, to_id, label, metadata) VALUES
-- Crown theft leads to shadow corruption spreading
('1d111111-1111-1111-1111-111111111111', '9d9d9d9d-9d9d-9d9d-9d9d-9d9d9d9d9d9d', '9e9e9e9e-9e9e-9e9e-9e9e-9e9e9e9e9e9e', 'caused', '{"causal_type": "magical_imbalance", "strength": "strong"}'),

-- Shadow corruption leads to Kael's fall
('1d222222-2222-2222-2222-222222222222', '9e9e9e9e-9e9e-9e9e-9e9e-9e9e9e9e9e9e', '22222222-2222-2222-2222-222222222222', 'corrupts', '{"causal_type": "personal_transformation", "strength": "strong"}'),

-- Crown theft necessitates the quest
('1d333333-3333-3333-3333-333333333333', '9d9d9d9d-9d9d-9d9d-9d9d-9d9d9d9d9d9d', '2a222222-2222-2222-2222-222222222222', 'necessitates', '{"causal_type": "plot_motivation", "strength": "strong"}'),

-- Heritage revelation changes quest understanding
('1d444444-4444-4444-4444-444444444444', '9f9f9f9f-9f9f-9f9f-9f9f-9f9f9f9f9f9f', '8b8b8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b', 'reveals', '{"causal_type": "knowledge_revelation", "strength": "medium"}'),

-- Quest beginning leads to party formation
('1d555555-5555-5555-5555-555555555555', '2a222222-2222-2222-2222-222222222222', '10111111-1111-1111-1111-111111111111', 'enables', '{"causal_type": "social_formation", "strength": "medium"}');

