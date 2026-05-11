"""game classes, for:
make, calculate and show pipe, bird, score, background and floor
"""
from random import randrange
from os.path import join
from constant import pygame, BEST_SCORE
from constant import WINDOW_HEIGHT, WINDOW_WIDTH, FLOOR_HEIGHT, PIPE_GAP
from constant import world, bird_images, numbers_img, scoreboard_img


def _load_font(size):
    """Load PressStart2P font with fallback to pygame default."""
    path = pygame.font.match_font('pressstart2p')
    if path:
        return pygame.font.Font(path, size)
    try:
        return pygame.font.Font(join('data', 'PressStart2P.ttf'), size)
    except Exception:
        return pygame.font.Font(None, size)


def _draw_shadow_text(surface, font, text, color, x, y, shadow_color=(70, 70, 70), offset=2):
    """Render text with a subtle grey shadow underneath."""
    shadow = font.render(text, True, shadow_color)
    surface.blit(shadow, (x + offset, y + offset))
    label = font.render(text, True, color)
    surface.blit(label, (x, y))


def make_powerless_surface(surface):
    """Create a dark monochrome copy once instead of filtering every frame."""
    powerless = pygame.transform.grayscale(surface).convert_alpha()
    powerless.fill((78, 78, 78, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return powerless


def blit_color_restored(window, color_surface, powerless_surface, position, color_amount):
    """Draw monochrome first, then fade the original color back in."""
    window.blit(powerless_surface, position)
    if color_amount <= 0:
        return

    color_surface.set_alpha(color_amount)
    window.blit(color_surface, position)
    color_surface.set_alpha(None)


def restore_color(color, color_amount):
    color_mix = max(0, min(255, color_amount)) / 255
    luminance = int((color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.114) * 0.78)
    return tuple(int(luminance * (1 - color_mix) + channel * color_mix) for channel in color)


class Ribbon:
    """Ribbon trail class for
    storing bird position history and drawing a fading ribbon behind it
    """

    def __init__(self, ribbon_image, max_segments=30):
        """Initialize the ribbon trail

        Args:
            ribbon_image (pygame surface): the ribbon sprite image
            max_segments (int): how many trail segments to keep (higher = longer trail)
        """
        self.ribbon_img = ribbon_image
        self.max_segments = max_segments
        self.segments = []
        self.alpha_decay = 255 / max_segments
        self.velocity = 6
        self.base_width = max(10, ribbon_image.get_height() * 0.3)
        self.tail_width = max(5, ribbon_image.get_height() * 0.3)

    def update(self, bird_x, bird_y, bird_width, bird_height):
        """Update ribbon trail with bird's current position"""
        for segment in self.segments:
            segment['x'] -= self.velocity

        ribbon_x = bird_x + (bird_width * 0.18)
        ribbon_y = bird_y + (bird_height / 2)

        new_segment = {
            'x': ribbon_x,
            'y': ribbon_y,
            'alpha': 255
        }
        self.segments.insert(0, new_segment)

        if len(self.segments) > self.max_segments:
            self.segments.pop()

        for i, segment in enumerate(self.segments):
            segment['alpha'] = max(0, 255 - (i * self.alpha_decay))

    def draw(self, window, color_amount=255):
        """Draw the ribbon as a continuous fading strip."""
        if len(self.segments) < 2:
            return

        ribbon_surface = pygame.Surface(window.get_size(), pygame.SRCALPHA)
        top_edge = []
        bottom_edge = []
        ribbon_path = self._smooth_path(self.segments)
        total = max(1, len(ribbon_path) - 1)

        for index, segment in enumerate(ribbon_path):
            prev_segment = ribbon_path[max(0, index - 1)]
            next_segment = ribbon_path[min(len(ribbon_path) - 1, index + 1)]
            dx = next_segment['x'] - prev_segment['x']
            dy = next_segment['y'] - prev_segment['y']
            length = max(1, (dx * dx + dy * dy) ** 0.5)
            normal_x = -dy / length
            normal_y = dx / length

            taper = 1 - (index / total)
            half_width = (self.tail_width + (self.base_width - self.tail_width) * taper) / 2
            x_pos = segment['x']
            y_pos = segment['y']
            top_edge.append((x_pos + normal_x * half_width, y_pos + normal_y * half_width))
            bottom_edge.append((x_pos - normal_x * half_width, y_pos - normal_y * half_width))

        for index in range(len(ribbon_path) - 1):
            fade = 1 - (index / total)
            body_alpha = int(35 + 125 * fade)
            edge_alpha = int(25 + 105 * fade)
            quad = [top_edge[index], top_edge[index + 1], bottom_edge[index + 1], bottom_edge[index]]
            pygame.draw.polygon(
                ribbon_surface,
                (*restore_color((105, 230, 95), color_amount), body_alpha),
                quad
            )
            pygame.draw.line(
                ribbon_surface,
                (*restore_color((230, 255, 225), color_amount), edge_alpha),
                top_edge[index],
                top_edge[index + 1],
                3
            )
            pygame.draw.line(
                ribbon_surface,
                (*restore_color((230, 255, 225), color_amount), edge_alpha),
                bottom_edge[index],
                bottom_edge[index + 1],
                3
            )

        pygame.draw.circle(
            ribbon_surface,
            (*restore_color((105, 230, 95), color_amount), 120),
            (round(ribbon_path[0]['x']), round(ribbon_path[0]['y'])),
            max(3, round(self.base_width / 2))
        )
        window.blit(ribbon_surface, (0, 0))

    def _smooth_path(self, points):
        """Round off sharp corners with a light Chaikin pass."""
        smoothed = points[:]
        for _ in range(2):
            if len(smoothed) < 3:
                break

            next_points = [smoothed[0]]
            for first, second in zip(smoothed, smoothed[1:]):
                next_points.append({
                    'x': first['x'] * 0.75 + second['x'] * 0.25,
                    'y': first['y'] * 0.75 + second['y'] * 0.25,
                    'alpha': first['alpha'],
                })
                next_points.append({
                    'x': first['x'] * 0.25 + second['x'] * 0.75,
                    'y': first['y'] * 0.25 + second['y'] * 0.75,
                    'alpha': second['alpha'],
                })
            next_points.append(smoothed[-1])
            smoothed = next_points
        return smoothed

    def reset(self):
        """Clear all segments"""
        self.segments = []


class FloatingText:
    """A small floating '+N' label that pops up when a note is collected."""
    _font = None

    def __init__(self, text, x, y):
        if FloatingText._font is None:
            FloatingText._font = _load_font(16)
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.vy = -2.0
        self.life = 55
        self.alpha = 255

    def update(self):
        self.y += self.vy
        self.life -= 1
        self.alpha = max(0, int(255 * self.life / 55))

    def draw(self, window):
        shadow = self._font.render(self.text, True, (70, 70, 70))
        shadow.set_alpha(self.alpha)
        window.blit(shadow, (int(self.x) + 2, int(self.y) + 2))
        surf = self._font.render(self.text, True, (210, 160, 255))
        surf.set_alpha(self.alpha)
        window.blit(surf, (int(self.x), int(self.y)))

    @property
    def dead(self):
        return self.life <= 0


class Score:
    """Score class — music note points meter with distance tracker.

    Goal: collect 25 points worth of notes (each note is worth 3, 4, or 5).
    """
    GOAL = 25
    numbers = numbers_img
    scoreboard = scoreboard_img
    _board_img = None
    _notepoints_img = None
    _font_med = None
    _font_sm = None

    HUD_W = 320
    HUD_H = 60
    BOARD_H = 90

    def __init__(self):
        self.note_points = 0
        self.distance = 0
        self.floating_texts = []
        if Score._notepoints_img is None:
            try:
                raw = pygame.image.load(join('data', 'notepoints.png')).convert_alpha()
                nw, nh = raw.get_size()
                natural_h = max(50, int(Score.HUD_W * nh / nw))
                Score._notepoints_img = pygame.transform.smoothscale(raw, (Score.HUD_W, natural_h))
                Score.HUD_H = natural_h
            except Exception:
                Score._notepoints_img = None
        if Score._board_img is None:
            try:
                raw = pygame.image.load(join('data', 'board.png')).convert_alpha()
                bw, bh = raw.get_size()
                # Board is taller than notepoints — it also covers the distance text row
                board_h = Score.HUD_H + 34
                Score._board_img = pygame.transform.smoothscale(raw, (Score.HUD_W, board_h))
                Score.BOARD_H = board_h
            except Exception:
                Score._board_img = None
        if Score._font_med is None:
            Score._font_med = _load_font(18)
        if Score._font_sm is None:
            Score._font_sm = _load_font(14)

    def add_score(self):
        """Legacy method — kept for compatibility."""
        pass

    def add_note_points(self, value, bird_x=0, bird_y=0):
        """Add note points and spawn a floating '+N' label."""
        self.note_points = min(self.note_points + value, self.GOAL)
        self.floating_texts.append(FloatingText(f'+{value}', bird_x + 40, bird_y))

    def update(self, distance_delta=0):
        """Advance the distance counter and tick floating texts."""
        self.distance += distance_delta
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if not ft.dead]

    def draw(self, window):
        """Draw the meter HUD using board.png + notepoints.png."""
        global BEST_SCORE
        hud_x, hud_y = 16, 16
        board_h = self._board_img.get_height() if self._board_img else self.HUD_H + 34

        # --- pill-shaped drop shadow that matches board.png ---
        shw = self.HUD_W + 8
        shh = board_h + 8
        shadow_surf = pygame.Surface((shw, shh), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 65),
                         (0, 0, shw, shh), border_radius=shh // 2)
        window.blit(shadow_surf, (hud_x + 3, hud_y + 5))

        # --- board.png (full-height background pill) ---
        if self._board_img:
            window.blit(self._board_img, (hud_x, hud_y))

        # --- progress fill — hard-clipped so it cannot overflow ---
        # bar rect targets the interior of notepoints dotted box
        bar_x = hud_x + int(self.HUD_W * 0.28)
        bar_y = hud_y + int(self.HUD_H * 0.12)
        bar_w = int(self.HUD_W * 0.70)
        bar_h = int(self.HUD_H * 0.76)
        fill_ratio = min(1.0, self.note_points / self.GOAL)
        fill_w = max(0, int(bar_w * fill_ratio))

        old_clip = window.get_clip()
        window.set_clip(pygame.Rect(bar_x, bar_y, bar_w, bar_h))
        if fill_w > 0:
            pygame.draw.rect(window, (150, 70, 200),
                             (bar_x, bar_y, fill_w, bar_h))
        window.set_clip(old_clip)

        # --- notepoints.png on top — its border frames the fill perfectly ---
        if self._notepoints_img:
            window.blit(self._notepoints_img, (hud_x, hud_y))

        # --- points text centred on bar ---
        pts_text = f'{self.note_points}/{self.GOAL}'
        tw, th = self._font_med.size(pts_text)
        cx = bar_x + bar_w // 2 - tw // 2
        cy = bar_y + bar_h // 2 - th // 2
        pts_shad = self._font_med.render(pts_text, True, (50, 50, 50))
        pts_surf = self._font_med.render(pts_text, True, (255, 255, 255))
        window.blit(pts_shad, (cx + 1, cy + 1))
        window.blit(pts_surf, (cx, cy))

        # --- distance text inside the board area below the notepoints image ---
        dist_m = self.distance // 60
        dist_text = f'{dist_m}m'
        _draw_shadow_text(window, self._font_sm, dist_text, (210, 185, 255),
                          hud_x + 10, hud_y + self.HUD_H + 6)

        # --- floating '+N' labels ---
        for ft in self.floating_texts:
            ft.draw(window)


def crop_to_opaque(surf):
    """Return a copy with transparent border pixels removed."""
    bounds = surf.get_bounding_rect()
    if bounds.width <= 0 or bounds.height <= 0:
        return surf

    cropped = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
    cropped.blit(surf, (0, 0), bounds)
    return cropped


class MusicNote:
    """A collectible musical note that lives inside a pipe gap."""

    NOTE_SIZE = 38
    _img = None
    _powerless_img = None

    def __init__(self, x_pos, y_pos):
        if MusicNote._img is None:
            raw = pygame.image.load(join('data', 'note.png')).convert_alpha()
            MusicNote._img = pygame.transform.scale(raw, (self.NOTE_SIZE, self.NOTE_SIZE))
            MusicNote._powerless_img = make_powerless_surface(MusicNote._img)

        self.img = MusicNote._img
        self.powerless_img = MusicNote._powerless_img
        self.x_pos = float(x_pos)
        self.y_pos = float(y_pos)
        self.collected = False
        self.point_value = randrange(3, 6)
        self.velocity = Pipe.velocity

        margin = 6
        self.rect = pygame.Rect(
            int(self.x_pos) + margin,
            int(self.y_pos) + margin,
            self.NOTE_SIZE - margin * 2,
            self.NOTE_SIZE - margin * 2,
        )

    def move(self):
        self.x_pos -= self.velocity
        self.rect.x = int(self.x_pos) + 6

    @property
    def off_screen(self):
        return self.x_pos + self.NOTE_SIZE < 0

    def check_collect(self, bird):
        if self.collected:
            return False

        bird_rect = pygame.Rect(
            bird.x_pos,
            round(bird.y_pos),
            bird.img.get_width(),
            bird.img.get_height()
        )
        if self.rect.colliderect(bird_rect):
            self.collected = True
            return self.point_value
        return False

    def draw(self, window, color_amount=255):
        if not self.collected:
            blit_color_restored(
                window,
                self.img,
                self.powerless_img,
                (int(self.x_pos), int(self.y_pos)),
                color_amount
            )


class DynamicLighting:
    """Manage the level's color returning as the run progresses."""

    def __init__(self):
        self.progress = 0.0
        self.start_x = 0
        self.end_x = 12000
        self.start_color = 0
        self.full_color = 255

    def update(self, progress_x):
        distance = max(0, progress_x - self.start_x)
        self.progress = min(1.0, distance / self.end_x)

    def get_alpha(self):
        eased_progress = self.progress * self.progress * (3 - 2 * self.progress)
        color_range = self.full_color - self.start_color
        return int(self.start_color + (color_range * eased_progress))


class VictoryPlatform:
    """Landing platform that appears at the end of the level."""

    velocity = 6

    def __init__(self, x_pos):
        self.x_pos = x_pos
        self.width = 300
        self.height = 60
        self.y_pos = WINDOW_HEIGHT - FLOOR_HEIGHT - self.height
        self.color = (100, 200, 100)
        self.edge_color = (255, 215, 0)
        self.is_active = False
        self.rect = pygame.Rect(self.x_pos, self.y_pos, self.width, self.height)

    def set_active(self):
        self.is_active = True

    def move(self):
        if not self.is_active:
            return
        self.x_pos -= self.velocity
        self.rect.x = round(self.x_pos)

    def check_landing(self, bird):
        if not self.is_active:
            return False

        bird_rect = pygame.Rect(
            bird.x_pos,
            round(bird.y_pos),
            bird.img.get_width(),
            bird.img.get_height()
        )
        bird_bottom = bird_rect.bottom
        platform_top = self.rect.top
        is_above_platform = bird_bottom <= platform_top + 18
        is_falling = bird.last_displacement >= 0

        return bird_rect.colliderect(self.rect) and is_above_platform and is_falling

    def draw(self, window, color_amount=255):
        if not self.is_active:
            return

        pygame.draw.rect(window, restore_color(self.color, color_amount), self.rect, border_radius=8)
        pygame.draw.rect(
            window,
            restore_color(self.edge_color, color_amount),
            self.rect,
            width=4,
            border_radius=8
        )


class Pipe:
    """Pipe class for
    set pipes height,
    move and draw pipes
    and check collide the bird to pipes
    """
    TOP_BUILDING_IMG = world['building_top']
    TOP_BUILDING_POWERLESS_IMG = world['building_top_powerless']
    BOTTOM_BUILDING_IMG = world['building_bottom']
    BOTTOM_BUILDING_POWERLESS_IMG = world['building_bottom_powerless']
    velocity = 6

    def __init__(self, x_pos):
        self.x_pos = x_pos
        self.passed = False
        self.set_height()
        self._spawn_note()

    def _make_building(self, image, target_width, target_height, flip_vertical=False):
        """Scale the building and crop transparent padding like the old version."""
        surf = pygame.transform.smoothscale(
            image,
            (target_width, target_height)
        )
        if flip_vertical:
            surf = pygame.transform.flip(surf, False, True)
        surf = crop_to_opaque(surf)
        return surf, make_powerless_surface(surf)

    def set_height(self):
        """Initialize one skyline segment with top and bottom buildings."""
        min_building_height = int(WINDOW_HEIGHT * 0.14)
        max_building_height = int(WINDOW_HEIGHT * 0.43)
        gap_size = PIPE_GAP + randrange(-35, 36)
        available_height = WINDOW_HEIGHT - gap_size

        bottom_min = max(min_building_height, available_height - max_building_height)
        bottom_max = min(max_building_height, available_height - min_building_height)
        if bottom_min > bottom_max:
            bottom_height = max(min_building_height, available_height // 2)
        else:
            bottom_height = randrange(bottom_min, bottom_max + 1)
        top_height = max(min_building_height, available_height - bottom_height)

        bottom_source_width, bottom_source_height = self.BOTTOM_BUILDING_IMG.get_size()
        bottom_target_width = max(1, int(bottom_height * bottom_source_width / bottom_source_height))
        top_source_width, top_source_height = self.TOP_BUILDING_IMG.get_size()
        top_target_width = max(1, int(top_height * top_source_width / top_source_height))

        self.bottom_building, self.bottom_building_powerless = self._make_building(
            self.BOTTOM_BUILDING_IMG, bottom_target_width, bottom_height)
        self.width = self.bottom_building.get_width()
        self.height = self.bottom_building.get_height()
        self.bottom_y = WINDOW_HEIGHT - self.height

        self.top_building, self.top_building_powerless = self._make_building(
            self.TOP_BUILDING_IMG, top_target_width, top_height, flip_vertical=True)
        self.bottom_mask = pygame.mask.from_surface(self.bottom_building)
        self.top_mask = pygame.mask.from_surface(self.top_building)
        self.top_height = self.top_building.get_height()
        self.top_draw_y = 0
        self.gap_top = self.top_height
        self.gap_bottom = self.bottom_y

        # Bottom collision rect based on non-transparent pixels
        bottom_bounds = self.bottom_building.get_bounding_rect()
        self.bottom_rect = pygame.Rect(
            self.x_pos + bottom_bounds.x,
            self.bottom_y + bottom_bounds.y,
            bottom_bounds.width,
            bottom_bounds.height
        )

        # Top collision rect based on non-transparent pixels
        top_bounds = self.top_building.get_bounding_rect()
        self.top_rect = pygame.Rect(
            self.x_pos + top_bounds.x,
            self.top_draw_y + top_bounds.y,
            top_bounds.width,
            top_bounds.height
        )

    def _spawn_note(self):
        note_size = MusicNote.NOTE_SIZE
        margin = 30
        gap_top = self.gap_top + margin
        gap_bottom = self.gap_bottom - margin - note_size

        if gap_bottom <= gap_top:
            self.note = None
            return

        note_y = randrange(gap_top, gap_bottom + 1)
        note_x = self.x_pos + (self.width // 2) - (note_size // 2)
        self.note = MusicNote(note_x, note_y)

    def move(self):
        self.x_pos -= self.velocity
        self.top_rect.x -= self.velocity
        self.bottom_rect.x -= self.velocity
        if self.note:
            self.note.move()

    def draw(self, window, color_amount=255):
        """draw skyline buildings in screen

        Args:
            window (pygame surface): display of the game
        """
        blit_color_restored(
            window,
            self.top_building,
            self.top_building_powerless,
            (self.x_pos, self.top_draw_y),
            color_amount
        )
        blit_color_restored(
            window,
            self.bottom_building,
            self.bottom_building_powerless,
            (self.x_pos, self.bottom_y),
            color_amount
        )
        if self.note:
            self.note.draw(window, color_amount)

    def check_note_collect(self, bird) -> bool:
        if self.note:
            return self.note.check_collect(bird)
        return False

    def collide(self, bird: object) -> bool:
        """check collide the bird to pipes

        Args:
            bird (object): bird class

        Returns:
            bool: True for collide and false for not collide
        """
        bird_rect = pygame.Rect(bird.x_pos, round(bird.y_pos), bird.img.get_width(), bird.img.get_height())
        bird_mask = pygame.mask.from_surface(bird.img)

        if self.top_rect.colliderect(bird_rect):
            top_offset = (
                round(bird.x_pos - self.x_pos),
                round(bird.y_pos - self.top_draw_y)
            )
            if self.top_mask.overlap(bird_mask, top_offset):
                return True

        if self.bottom_rect.colliderect(bird_rect):
            bottom_offset = (
                round(bird.x_pos - self.x_pos),
                round(bird.y_pos - self.bottom_y)
            )
            if self.bottom_mask.overlap(bird_mask, bottom_offset):
                return True

        return False


class Bird:
    """Bird class for
    bird jump,
    change tilt
    check crashed,
    move the bird(change bird position),
    set state of bird image(idle, ascend, descend)
    draw the bird in screen
    and get mask(for collide in Pipe model)
    """
    img = bird_images['idle']
    crashed = False
    FLAPS_ANIMATION_TIME = 5
    ROTATE_VEL = 10
    JUMP_STRENGTH = -9.6
    ASCENT_GRAVITY = 2
    DESCENT_GRAVITY = 1.25
    MAX_FALL_SPEED = 16

    def __init__(self, x_pos, y_pos, ribbon=None):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.tilt = 0
        self.tick = 0
        self.frame_index = 0
        self.velacity = 0
        self.height = self.y_pos
        self.ribbon = ribbon
        self.is_celebrating = False
        self.celebration_tick = 0
        self.last_displacement = 0

    def jump(self):
        """jump the bird in screen
        """
        self.velacity = self.JUMP_STRENGTH
        self.tick = 0
        self.height = self.y_pos

    def celebration_jump(self):
        """Start the automatic victory celebration."""
        self.is_celebrating = True
        self.celebration_tick = 0
        self.velacity = -12
        self.tick = 0

    def tilt_bird(self, displacement):
        """No tilt."""
        self.tilt = 0

    def check_crashed(self):
        """check for crashed bird, if it falls or goes up a lot
        """
        if self.y_pos >= WINDOW_HEIGHT:
            self.crashed = True

        if self.y_pos < - self.img.get_height() / 4:
            self.crashed = True

    def move(self):
        """move bird in screen with displacement value
        """
        if self.is_celebrating:
            self.celebration_tick += 1
            if self.celebration_tick % 30 == 0:
                self.jump()
            if self.celebration_tick >= 120:
                self.is_celebrating = False

        self.tick += 1
        ascent_displacement = self.velacity * self.tick + self.ASCENT_GRAVITY * self.tick ** 2
        gravity = self.ASCENT_GRAVITY if ascent_displacement < 0 else self.DESCENT_GRAVITY
        displacement = self.velacity * self.tick + gravity * self.tick ** 2
        if displacement >= self.MAX_FALL_SPEED:
            displacement = (displacement/abs(displacement)) * self.MAX_FALL_SPEED

        self.last_displacement = displacement
        self.y_pos += displacement

        self.tilt_bird(displacement)
        self.check_crashed()

        # Update ribbon trail if it exists
        if self.ribbon:
            self.ribbon.update(self.x_pos, self.y_pos, self.img.get_width(), self.img.get_height())

    def set_state(self):
        """Single-sprite character: no animation frames."""
        self.img = bird_images['idle']
        self.powerless_img = bird_images['idle_powerless']

    def draw(self, window, color_amount=255):
        """Draw the bird (single sprite, no rotation)."""
        self.set_state()
        blit_color_restored(
            window,
            self.img,
            self.powerless_img,
            (self.x_pos, self.y_pos),
            color_amount
        )


class Background:
    """Background class for,
    move and draw backgrounds (3 parallax layers: backBG, midBG, frontBG)
    """
    img_back = world['backBG']
    img_back_powerless = world['backBG_powerless']
    img_mid = world['midBG']
    img_mid_powerless = world['midBG_powerless']
    img_front = world['frontBG']
    img_front_powerless = world['frontBG_powerless']
    width = img_back.get_width()
    velocity = 1

    def __init__(self):
        self.back_x1 = 0
        self.back_x2 = self.width
        self.mid_x1 = 0
        self.mid_x2 = self.width
        self.front_x1 = 0
        self.front_x2 = self.width

    def move(self):
        """move backgrounds with velocity
        """
        self.back_x1 -= self.velocity
        self.back_x2 -= self.velocity
        self.mid_x1 -= self.velocity
        self.mid_x2 -= self.velocity
        self.front_x1 -= self.velocity
        self.front_x2 -= self.velocity

        if self.back_x1 + self.width < 0:
            self.back_x1 = self.back_x2 + self.width
        if self.back_x2 + self.width < 0:
            self.back_x2 = self.back_x1 + self.width
        if self.mid_x1 + self.width < 0:
            self.mid_x1 = self.mid_x2 + self.width
        if self.mid_x2 + self.width < 0:
            self.mid_x2 = self.mid_x1 + self.width
        if self.front_x1 + self.width < 0:
            self.front_x1 = self.front_x2 + self.width
        if self.front_x2 + self.width < 0:
            self.front_x2 = self.front_x1 + self.width

    def draw(self, window, color_amount=255):
        """draw backgrounds in screen

        Args:
            window (pygame surface): game display
        """
        blit_color_restored(
            window,
            self.img_back,
            self.img_back_powerless,
            (self.back_x1, 0),
            color_amount
        )
        blit_color_restored(
            window,
            self.img_back,
            self.img_back_powerless,
            (self.back_x2, 0),
            color_amount
        )

        # Draw midBG at the bottom of screen
        mid_y = WINDOW_HEIGHT - self.img_mid.get_height()
        blit_color_restored(
            window,
            self.img_mid,
            self.img_mid_powerless,
            (self.mid_x1, mid_y),
            color_amount
        )
        blit_color_restored(
            window,
            self.img_mid,
            self.img_mid_powerless,
            (self.mid_x2, mid_y),
            color_amount
        )

        # Draw frontBG a little higher than midBG
        front_y = WINDOW_HEIGHT - self.img_mid.get_height() - self.img_front.get_height()
        blit_color_restored(
            window,
            self.img_front,
            self.img_front_powerless,
            (self.front_x1, front_y),
            color_amount
        )
        blit_color_restored(
            window,
            self.img_front,
            self.img_front_powerless,
            (self.front_x2, front_y),
            color_amount
        )


class Floor:
    """Floor class for,
    move and draw floors
    """
    img = world['floor']
    width = img.get_width()
    height = img.get_height()
    velocity = 6

    def __init__(self):
        self.floor_x1 = 0
        self.floor_x2 = self.width

    def move(self):
        """move floor in screen with velocity
        """
        self.floor_x1 -= self.velocity
        self.floor_x2 -= self.velocity

        if self.floor_x1 + self.width < 0:
            self.floor_x1 = self.floor_x2 + self.width
        if self.floor_x2 + self.width < 0:
            self.floor_x2 = self.floor_x1 + self.width

    def draw(self, window, color_amount=255):
        """Draw floor to screen

        Args:
            window (pygame surface): game display
        """
        # Floor sprite hidden; keep the object for movement/game-loop compatibility.
        return
