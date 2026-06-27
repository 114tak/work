import sys
import pygame

pygame.init()
pygame.mixer.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")
clock = pygame.time.Clock()

# 色の定義
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
PINK = (230, 80, 170)
DARK_GRAY = (20, 20, 20)
PANEL_GRAY = (10, 10, 10)

# プレイヤー
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 16
PLAYER_SPEED = 5
PLAYER_LIVES = 3

# 弾
BULLET_WIDTH = 4
BULLET_HEIGHT = 12
BULLET_SPEED = 14
MAX_BULLETS = 3
SHOOT_COOLDOWN = 250  # ms

# 敵
INVADER_WIDTH = 32
INVADER_HEIGHT = 24
INVADER_ROWS = 5
INVADER_COLS = 10
INVADER_X_PADDING = 14
INVADER_Y_PADDING = 12
INVADER_TOP_MARGIN = 60
INVADER_LEFT_MARGIN = 40
INVADER_SPEED = 1
INVADER_DROP = 28
INVADER_COLORS = [GREEN, (0, 200, 255), PINK]

# フォント
font = pygame.font.SysFont("Consolas", 20)
large_font = pygame.font.SysFont("Consolas", 58)
small_font = pygame.font.SysFont("Consolas", 16)

# 盾
SHIELD_COUNT = 4
SHIELD_WIDTH = 80
SHIELD_HEIGHT = 40
SHIELD_Y = SCREEN_HEIGHT - 140

# 効果音
shoot_sound = None
try:
    shoot_sound = pygame.mixer.Sound("c:/work/game/sounds/laser.wav")
except Exception:
    shoot_sound = None


def create_invaders():
    invaders = []
    for row in range(INVADER_ROWS):
        for col in range(INVADER_COLS):
            x = INVADER_LEFT_MARGIN + col * (INVADER_WIDTH + INVADER_X_PADDING)
            y = INVADER_TOP_MARGIN + row * (INVADER_HEIGHT + INVADER_Y_PADDING)
            invader_rect = pygame.Rect(x, y, INVADER_WIDTH, INVADER_HEIGHT)
            color = INVADER_COLORS[row // 2 % len(INVADER_COLORS)]
            invaders.append({"rect": invader_rect, "color": color, "row": row})
    return invaders


def create_shields():
    shields = []
    spacing = (SCREEN_WIDTH - 160) // (SHIELD_COUNT - 1)
    start_x = 80
    for index in range(SHIELD_COUNT):
        x = start_x + index * spacing
        shields.append(pygame.Rect(x, SHIELD_Y, SHIELD_WIDTH, SHIELD_HEIGHT))
    return shields


def draw_text(surface, text, color, x, y, font_obj):
    rendered = font_obj.render(text, True, color)
    surface.blit(rendered, (x, y))


def draw_right_panel():
    panel_width = 200
    panel_x = SCREEN_WIDTH - panel_width
    pygame.draw.rect(screen, PANEL_GRAY, (panel_x, 0, panel_width, SCREEN_HEIGHT))
    draw_text(screen, "HIGH SCORE", WHITE, panel_x + 20, 40, small_font)
    draw_text(screen, f"{high_score:05d}", WHITE, panel_x + 20, 70, font)
    draw_text(screen, "1UP", WHITE, panel_x + 20, 140, font)
    draw_text(screen, f"{score:05d}", WHITE, panel_x + 20, 170, font)
    draw_text(screen, "2UP", WHITE, panel_x + 20, 240, font)
    draw_text(screen, "00000", WHITE, panel_x + 20, 270, font)
    draw_text(screen, "ROUND", WHITE, panel_x + 20, 340, font)
    draw_text(screen, f"{round_num:02d}", WHITE, panel_x + 20, 370, font)


def reset_game():
    player = pygame.Rect((SCREEN_WIDTH - PLAYER_WIDTH) // 2,
                         SCREEN_HEIGHT - PLAYER_HEIGHT - 24,
                         PLAYER_WIDTH, PLAYER_HEIGHT)
    bullets = []
    invaders = create_invaders()
    shields = create_shields()
    invader_dx = INVADER_SPEED
    return player, bullets, invaders, shields, invader_dx


def draw_invader(rect, color):
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, BLACK, (rect.x + 4, rect.y + 4, rect.width - 8, rect.height - 8))


def main():
    global score, high_score, round_num
    score = 0
    high_score = 5000
    round_num = 1

    player, bullets, invaders, shields, invader_dx = reset_game()
    running = True
    game_over = False
    victory = False
    last_shot_time = 0

    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and game_over:
                    score = 0
                    round_num = 1
                    player, bullets, invaders, shields, invader_dx = reset_game()
                    game_over = False
                    victory = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not game_over:
                    if len(bullets) < MAX_BULLETS and current_time - last_shot_time >= SHOOT_COOLDOWN:
                        bullet_x = player.centerx - BULLET_WIDTH // 2
                        bullet_y = player.top - BULLET_HEIGHT
                        bullets.append(pygame.Rect(bullet_x, bullet_y, BULLET_WIDTH, BULLET_HEIGHT))
                        last_shot_time = current_time
                        if shoot_sound is not None:
                            shoot_sound.play()

        if not game_over:
            mouse_x, _ = pygame.mouse.get_pos()
            target_x = mouse_x - PLAYER_WIDTH // 2
            if target_x < 0:
                target_x = 0
            if target_x > SCREEN_WIDTH - 200 - PLAYER_WIDTH:
                target_x = SCREEN_WIDTH - 200 - PLAYER_WIDTH
            player.x = target_x

            for bullet in bullets[:]:
                bullet.y -= BULLET_SPEED
                if bullet.bottom < 0:
                    bullets.remove(bullet)

            should_reverse = False
            for invader in invaders:
                if invader["rect"].right >= SCREEN_WIDTH - 200 or invader["rect"].left <= 0:
                    should_reverse = True
                    break

            if should_reverse:
                invader_dx *= -1
                for invader in invaders:
                    invader["rect"].y += INVADER_DROP

            for invader in invaders:
                invader["rect"].x += invader_dx

            for bullet in bullets[:]:
                for invader in invaders[:]:
                    if bullet.colliderect(invader["rect"]):
                        bullets.remove(bullet)
                        invaders.remove(invader)
                        score += 50
                        break

            for shield in shields[:]:
                for bullet in bullets[:]:
                    if shield.colliderect(bullet):
                        bullets.remove(bullet)
                        break

            for invader in invaders[:]:
                for shield in shields[:]:
                    if invader["rect"].colliderect(shield):
                        shields.remove(shield)
                        break

            for invader in invaders:
                if invader["rect"].bottom >= player.top:
                    game_over = True
                    break

            if not invaders:
                victory = True
                game_over = True

        screen.fill(BLACK)

        pygame.draw.rect(screen, PANEL_GRAY, (SCREEN_WIDTH - 200, 0, 200, SCREEN_HEIGHT))
        draw_text(screen, "HIGH SCORE", WHITE, SCREEN_WIDTH - 180, 40, small_font)
        draw_text(screen, f"{high_score:05d}", WHITE, SCREEN_WIDTH - 180, 70, font)
        draw_text(screen, "1UP", WHITE, SCREEN_WIDTH - 180, 140, font)
        draw_text(screen, f"{score:05d}", WHITE, SCREEN_WIDTH - 180, 170, font)
        draw_text(screen, "2UP", WHITE, SCREEN_WIDTH - 180, 240, font)
        draw_text(screen, "00000", WHITE, SCREEN_WIDTH - 180, 270, font)
        draw_text(screen, "ROUND", WHITE, SCREEN_WIDTH - 180, 340, font)
        draw_text(screen, f"{round_num:02d}", WHITE, SCREEN_WIDTH - 180, 370, font)

        draw_text(screen, "PRESS SPACE", WHITE, SCREEN_WIDTH - 180, SCREEN_HEIGHT - 120, small_font)
        draw_text(screen, "TO SHOOT", WHITE, SCREEN_WIDTH - 180, SCREEN_HEIGHT - 100, small_font)

        draw_text(screen, f"LIVES", WHITE, SCREEN_WIDTH - 180, SCREEN_HEIGHT - 70, small_font)
        for i in range(PLAYER_LIVES):
            life_x = SCREEN_WIDTH - 100 + i * 24
            pygame.draw.polygon(screen, BLUE, [(life_x, SCREEN_HEIGHT - 40),
                                              (life_x + 10, SCREEN_HEIGHT - 50),
                                              (life_x + 20, SCREEN_HEIGHT - 40),
                                              (life_x + 12, SCREEN_HEIGHT - 34),
                                              (life_x + 8, SCREEN_HEIGHT - 34)])

        for shield in shields:
            pygame.draw.rect(screen, RED, shield)
            pygame.draw.rect(screen, BLACK, shield, 2)

        pygame.draw.rect(screen, BLUE, player)
        pygame.draw.rect(screen, BLACK, player, 2)

        for bullet in bullets:
            pygame.draw.rect(screen, YELLOW, bullet)

        for invader in invaders:
            draw_invader(invader["rect"], invader["color"])

        if game_over:
            message = "ROUND CLEAR" if victory else "GAME OVER"
            draw_text(screen, message, RED if not victory else GREEN,
                      240, SCREEN_HEIGHT // 2 - 40, large_font)
            draw_text(screen, "PRESS R TO RESTART", WHITE,
                      240, SCREEN_HEIGHT // 2 + 40, font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
