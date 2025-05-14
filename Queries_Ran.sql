create table users (
    id serial primary key,
    username varchar(50) unique not null,
    password varchar(255) not null,
    role varchar(20) not null,
    created_at timestamp default current_timestamp
);

create table games (
    id serial primary key,
    name varchar(50) unique not null
);

create table player_games (
    player_id integer references users(id),
    game_id integer references games(id),
    primary key (player_id, game_id)
);

create table teams (
    id serial primary key,
    name varchar(100) unique not null,
    created_at timestamp default current_timestamp
);

create table team_members (
    team_id integer references teams(id),
    player_id integer references users(id),
    joined_at timestamp default current_timestamp,
    primary key (team_id, player_id)
);

create table tournaments (
    id serial primary key,
    name varchar(100) not null,
    game_id integer references games(id),
    created_by integer references users(id),
    created_at timestamp default current_timestamp,
    winner_id integer references users(id)
);

create table tournament_participants (
    tournament_id integer references tournaments(id),
    player_id integer references users(id),
    registered_at timestamp default current_timestamp,
    primary key (tournament_id, player_id)
);

create table matches (
    id serial primary key,
    game_id integer references games(id),
    player1_id integer references users(id),
    player2_id integer references users(id),
    winner_id integer references users(id),
    match_type varchar(20) not null,
    created_at timestamp default current_timestamp
);

create table player_stats (
    player_id integer references users(id),
    tournaments_won integer default 0,
    matches_won integer default 0,
    total_matches integer default 0,
    primary key (player_id)
);

insert into games (name) values 
    ('dota2'),
    ('fortnite'),
    ('valorant'),
    ('fifa'),
    ('cod'),
    ('tekken'),
    ('league of legends')
on conflict (name) do nothing;

insert into users (username, password, role)
values ('admin', 'admin', 'admin')
on conflict (username) do nothing;

create index idx_users_username on users(username);
create index idx_teams_name on teams(name);
create index idx_tournaments_name on tournaments(name);
create index idx_matches_players on matches(player1_id, player2_id);
create index idx_player_games_player on player_games(player_id);
create index idx_team_members_player on team_members(player_id);
create index idx_tournament_participants_player on tournament_participants(player_id);


select * from tournaments

-- backup tables 


create table users_backup (
    id serial primary key,
    username varchar(50) unique not null,
    password varchar(255) not null,
    role varchar(20) not null,
    created_at timestamp default current_timestamp
);

create table games_backup (
    id serial primary key,
    name varchar(50) unique not null
);

create table player_games_backup (
    player_id integer references users(id),
    game_id integer references games(id),
    primary key (player_id, game_id)
);

create table teams_backup (
    id serial primary key,
    name varchar(100) unique not null,
    created_at timestamp default current_timestamp
);

create table team_members_backup (
    team_id integer references teams(id),
    player_id integer references users(id),
    joined_at timestamp default current_timestamp,
    primary key (team_id, player_id)
);

create table tournaments_backup (
    id serial primary key,
    name varchar(100) not null,
    game_id integer references games(id),
    created_by integer references users(id),
    created_at timestamp default current_timestamp,
    winner_id integer references users(id)
);

create table tournament_participants_backup (
    tournament_id integer references tournaments(id),
    player_id integer references users(id),
    registered_at timestamp default current_timestamp,
    primary key (tournament_id, player_id)
);

create table matches_backup (
    id serial primary key,
    game_id integer references games(id),
    player1_id integer references users(id),
    player2_id integer references users(id),
    winner_id integer references users(id),
    match_type varchar(20) not null,
    created_at timestamp default current_timestamp
);

create table player_stats_backup (
    player_id integer references users(id),
    tournaments_won integer default 0,
    matches_won integer default 0,
    total_matches integer default 0,
    primary key (player_id)
);

--triggers and functions, the insert the deleted value into the backup table from the main table


-- users
create or replace function backup_users() returns trigger as $$
begin
    insert into users_backup (id, username, password, role, created_at)
    values (old.id, old.username, old.password, old.role, old.created_at);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_users
before delete on users
for each row execute function backup_users();

-- games
create or replace function backup_games() returns trigger as $$
begin
    insert into games_backup (id, name)
    values (old.id, old.name);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_games
before delete on games
for each row execute function backup_games();

-- player_games
create or replace function backup_player_games() returns trigger as $$
begin
    insert into player_games_backup (player_id, game_id)
    values (old.player_id, old.game_id);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_player_games
before delete on player_games
for each row execute function backup_player_games();

-- teams
create or replace function backup_teams() returns trigger as $$
begin
    insert into teams_backup (id, name, created_at)
    values (old.id, old.name, old.created_at);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_teams
before delete on teams
for each row execute function backup_teams();

-- team_members
create or replace function backup_team_members() returns trigger as $$
begin
    insert into team_members_backup (team_id, player_id, joined_at)
    values (old.team_id, old.player_id, old.joined_at);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_team_members
before delete on team_members
for each row execute function backup_team_members();

-- tournaments
create or replace function backup_tournaments() returns trigger as $$
begin
    insert into tournaments_backup (id, name, game_id, created_by, created_at, winner_id)
    values (old.id, old.name, old.game_id, old.created_by, old.created_at, old.winner_id);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_tournaments
before delete on tournaments
for each row execute function backup_tournaments();

-- tournament_participants
create or replace function backup_tournament_participants() returns trigger as $$
begin
    insert into tournament_participants_backup (tournament_id, player_id, registered_at)
    values (old.tournament_id, old.player_id, old.registered_at);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_tournament_participants
before delete on tournament_participants
for each row execute function backup_tournament_participants();

-- matches
create or replace function backup_matches() returns trigger as $$
begin
    insert into matches_backup (id, game_id, player1_id, player2_id, winner_id, match_type, created_at)
    values (old.id, old.game_id, old.player1_id, old.player2_id, old.winner_id, old.match_type, old.created_at);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_matches
before delete on matches
for each row execute function backup_matches();

-- player_stats
create or replace function backup_player_stats() returns trigger as $$
begin
    insert into player_stats_backup (player_id, tournaments_won, matches_won, total_matches)
    values (old.player_id, old.tournaments_won, old.matches_won, old.total_matches);
    return old;
end;
$$ language plpgsql;

create trigger trg_backup_player_stats
before delete on player_stats
for each row execute function backup_player_stats();

insert into users (username, password, role)
values ('player', 'gaming', 'player')
on conflict (username) do nothing;         

insert into player_stats(player_id,tournaments_won,matches_won,total_matches)
values(2,0,0,0);


select* from users

select* from player_stats

-- Insert players (users)
INSERT INTO users (username, password, role) VALUES
('Arsalan Ash', '129', 'player'),
('TFue', 'pass123', 'player'),
('Ninja Tyler', 'password', 'player'),
('W2S', 'powder', 'player'),
('Tobi Brown', 'ggmu', 'player'),
('Josh Zerka', 'old', 'player'),
('Simon Minter', 'mm7', 'player'),
('Vikkstar123', 'india', 'player'),
('Shroud', 'pubg', 'player'),
('Dr Lupo', 'chugjug', 'player');

-- Insert teams
INSERT INTO teams (name) VALUES
('Sidemen'),
('Beta Squad'),
('Faze Clan'),
('Dude Perfect'),
('Biased Beasts');

-- Insert team members 
INSERT INTO team_members (team_id, player_id) VALUES
(1, 2),  
(1, 3), 
(2, 4),  
(2, 5),  
(3, 6),  
(3, 7),  
(4, 8), 
(4, 9),  
(5, 10), 
(5, 11); 


-- Insert player games (players and their chosen games)
INSERT INTO player_games (player_id, game_id) VALUES
(4, 1),  
(4, 3),  
(5, 2), 
(5, 4),  
(6, 1),  
(7, 3),  
(8, 5),  
(9, 6),  
(10, 7),  
(11, 1),  
(12, 2), 
(13, 3); 

-- Insert tournaments
INSERT INTO tournaments (name, game_id, created_by) VALUES
('Summer Dota Championship', 1, 1),
('Fortnite Masters', 2, 1),
('Valorant Pro League', 3, 1),
('FIFA World Cup', 4, 1),
('COD Tournament', 5, 1);

-- Insert tournament participants
INSERT INTO tournament_participants (tournament_id, player_id) VALUES
(1, 4),  
(1, 6),  
(1, 11),  
(2, 5),  
(2, 12), 
(3, 4),  
(3, 7),  
(3, 13), 
(4, 5),  
(5, 8);  

-- Insert matches
INSERT INTO matches (game_id, player1_id, player2_id, winner_id, match_type) VALUES
(1, 4, 6, 4, 'tournament'),    
(1, 11, 4, 4, 'tournament'),   
(2, 5, 12, 5, 'tournament'),   
(3, 4, 7, 7, 'tournament'),    
(3, 7, 13, 13, 'tournament'),  
(4, 5, 7, 5, 'friendly'),      
(5, 8, 9, 8, 'friendly'),      
(6, 9, 10, 9, 'friendly'),      
(7, 10, 11, 10, 'friendly'),      
(1, 4, 11 , 11, 'friendly');      


INSERT INTO player_stats (player_id, tournaments_won, matches_won, total_matches) VALUES
(4, 1, 2, 4),
(5, 1, 2, 2),
(6, 0, 0, 1),
(7, 0, 1, 2),
(8, 0, 1, 1),
(9, 0, 1, 2),
(10, 0, 1, 2), 
(11, 0, 1, 2),  
(12, 0, 0, 1),  
(13, 0, 1, 1);   