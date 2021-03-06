#!/usr/bin/env python
#-*- coding: utf-8 -*-

import glob

from PIL import Image
from PIL import ImageDraw
from PIL import ImageColor
import mgz
from mgz.summary import Summary
from mgz.const import MAP_SIZES

map_sizes = dict(zip(MAP_SIZES.values(),MAP_SIZES.keys()))
player_colors = ('#0000DD', '#ff0000', '#00ff00', '#ffff00', '#00ffff', '#ff00ff', '#E9E9E9', '#ff8201')

def draw_point(canvas, x, y, color):
    '''Points the initial player position with a special large circle'''
    player_color = player_colors[color]
    x1,y1,x2,y2 = (x-5, y-5, x+5, y+5)
    draw = ImageDraw.Draw(canvas)
    far = 6
    draw.ellipse((x1,y1, x2, y2), fill=player_color)
    draw.ellipse((x1-far,y1-far, x2+far, y2+far), outline=player_color, width=3)

def get_savedgames() -> ['recordedgames_file_names.valid_extension']:
    '''Gets file names with valid extensions'''
    recorded_games = []
    supported_extensions = ('.mgl', '.mgx', '.mgz', '.aoe2record')
    for recorded_game in range(len(supported_extensions)):
        if glob.glob('*'+supported_extensions[recorded_game]):
            recorded_games += glob.glob('*'+supported_extensions[recorded_game])
    return recorded_games

def to_rgb(farbe: str) -> tuple(['rrr','ggg','bbb']):
    '''Transforms an hex color value to a rgb color value'''
    return tuple(int(farbe[i:i+2], 16) for i in (0, 2, 4))

def get_data_from(input_file: str):
    '''Gets a summary'''
    with open(f'{input_file}', 'rb') as data:
        return Summary(data)

def new_canvas(map_size):
    return Image.new('RGBA', (map_size, map_size))

def draw_terrain(canvas, map_info, total_tiles):
    tiles_colors = ('#339727', '#305db6', '#e8b478', '#e4a252', '#5492b0',
                    '#339727', '#e4a252', '#82884d', '#82884d', '#339727',
                    '#157615', '#e4a252', '#339727', '#157615', '#e8b478',
                    '#305db6', '#339727', '#157615', '#157615', '#157615',
                    '#157615', '#157615', '#004aa1', '#004abb', '#e4a252',
                    '#e4a252', '#ffec49', '#e4a252', '#305db6', '#82884d',
                    '#82884d', '#82884d', '#c8d8ff', '#c8d8ff', '#c8d8ff',
                    '#98c0f0', '#c8d8ff', '#98c0f0', '#c8d8ff', '#c8d8ff',
                    '#e4a252')
    x,y = (0,0)
    for i in range(total_tiles):
        x = map_info['tiles'][i]['x']
        y = map_info['tiles'][i]['y']
        terrain = map_info['tiles'][i]['terrain_id'] 
        canvas.putpixel((x,y), to_rgb((tiles_colors[terrain])[1:]))

def draw_resources(canvas, resources):
    for resource in resources:
        if resource['object_type'] in [59, 833, 594, 65, 48, 810, 1026, 822, 1031, 1139, 69, 455, 456, 458, 457, 450, 451, 452]: # Food: berry_bush, fish, other animals.
            canvas.putpixel( (int(resource['x']), int(resource['y'])), to_rgb('A5C46C'))
            
        if resource['object_type'] == 102: # Stone pile
            canvas.putpixel( (int(resource['x']), int(resource['y'])), to_rgb('919191'))
            
        if resource['object_type'] == 66: # Gold pile
            canvas.putpixel( (int(resource['x']), int(resource['y'])), to_rgb('FFC700'))
            
        if resource['object_type'] == 285: # Relic
            canvas.putpixel( (int(resource['x']), int(resource['y'])), to_rgb('FFFFFF'))
            canvas.putpixel( (int(resource['x']+1), int(resource['y'])), to_rgb('FFFFFF'))
            canvas.putpixel( (int(resource['x']), int(resource['y'])+1), to_rgb('FFFFFF'))
            canvas.putpixel( (int(resource['x']-1), int(resource['y'])), to_rgb('FFFFFF'))
            canvas.putpixel( (int(resource['x']), int(resource['y'])-1), to_rgb('FFFFFF'))

def draw_players(canvas, players):
    for player in players:
        for coordinates in player:
            x = player['position'][0]
            y = player['position'][1]
            draw_point(canvas, x, y, player['color_id'])

def draw_walls(canvas, objects, players):
    '''Draws the walls according to:
        72 -> Palisade wall.
        117 -> Stone wall.
        155 -> Fortified wall.
        64, 81, 88, 95 -> Stone gate.
        662, 666, 670, 674 -> Palisade gate.
    '''
    for obj in objects.get('objects'):
        if obj['object_id'] in [72, 117, 155, 64, 81, 88, 95, 662, 666, 670, 674]:
            canvas.putpixel( (int(obj['x']), int(obj['y'])), to_rgb(player_colors[players[obj['player_number']-1]['color_id']][1:]))

def get_image(canvas, output_file_name):
    final_image = Image.new("RGBA", (300,200), (0,0,0,0))
    final_image.paste(canvas, (0, 0), canvas)
    final_image.save(f'./static/{output_file_name}')
    return final_image

def rotate(canvas, angle):
    return canvas.rotate(angle, resample=Image.BICUBIC, expand=True)

def resize(canvas, size):
    return canvas.resize(size)

def get_info(input_file:str, sumario):
    info = dict()
    info['nombre_archivo'] = input_file
    info['duracion_partida'] = mgz.util.convert_to_timestamp(sumario.get_duration()/1000)
    info['punto_de_vista'] = sumario.get_players()[sumario.get_owner()-1]['name']
    info['mapa_revelado'] = en_es['reveal_map'][sumario.get_settings()['map_reveal_choice'][1].capitalize()]
    info['velocidad'] = en_es['game_speeds'][sumario.get_settings()['speed'][1].capitalize()]
    info['poblacion'] = sumario.get_settings()['population_limit']
    info['diplomacia'] = sumario.get_diplomacy()['type']
    try:
        info['nombre_mapa'] = en_es['map_names'][sumario.get_map()['name']]
    except KeyError:
        info['nombre_mapa'] = sumario.get_map()['name']
    info['tamano_mapa'] = sumario.get_map()['size'].capitalize()
    info['bloqueo_diplomacia_equipos'] = 1 if sumario.get_settings()['lock_teams'] else 0
    info['dificultad'] = en_es['difficulties'][sumario.get_settings()['difficulty'][1].capitalize()]
    
    for map_size in en_es['map_sizes'].keys():
            if info['tamano_mapa'] in map_size:
                    info['tamano_mapa'] = en_es['map_sizes'][map_size]
                    
    info['teams'] = ''
    if info['diplomacia'] == 'TG':
        info['teams'] = sumario.get_diplomacy()['team_size']
        info['diplomacia'] = 'Batalla de equipos'
        
    equipos = dict()
    for index, team in enumerate(sumario.get_teams()):
        index += 1
        equipos[index] = dict()

        for jugador in team:
            equipos[index][jugador] = dict()
            equipos[index][jugador]['nickname'] = sumario.get_players()[jugador-1]['name']

            civ_cod = str(sumario.get_players()[jugador-1]['civilization'])
            civ = sumario.reference['civilizations'][civ_cod]['name']

            equipos[index][jugador]['civ_cod'] = civ_cod
            equipos[index][jugador]['civ'] = en_es['civilizations'][civ]

            if sumario.get_players()[jugador-1]['winner']:
                equipos[index][jugador]['victoria'] = 0 # False
            else:
                equipos[index][jugador]['victoria'] = 1 # True

            id_color = str(sumario.get_players()[jugador-1]['color_id'])
            equipos[index][jugador]['color_cod'] = id_color

            equipos[index][jugador]['color'] = mgz.reference.get_consts()['player_colors'][id_color]

    info['equipos'] = equipos

    return info

def write_minimap(input_file: str) -> 'minimap_{file_name}.png':
    '''Generates the minimap'''
    print(input_file)
    summary = get_data_from(input_file)
    all_info = get_info(input_file, summary)
    resources = summary.get_header()['initial']['players'][0]['objects']
    map_info = summary.get_map()
    players = summary.get_players()
    objects = summary.get_objects()
    
    map_size = map_sizes[map_info['size']]
    canvas = new_canvas(map_size)
    total_tiles = map_size ** 2
    
    draw_terrain(canvas, map_info, total_tiles)
    draw_resources(canvas, resources)
    draw_players(canvas, players)
    draw_walls(canvas, objects, players)

    angle = 45
    canvas = rotate(canvas, angle)
    canvas = resize(canvas, (300,200))

    output_file_name = f'minimap_{input_file[:-4]}.png'
    minimap = get_image(canvas, output_file_name)
    #minimap.show()
    return all_info
    
if __name__== "__main__":
    for rec in get_savedgames():
        write_minimap(rec)
    from en_to_es import en_es
else:
    from static.en_to_es import en_es
