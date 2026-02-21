import pygame
import random
import math
import os

# Инициализация Pygame
pygame.init()

# Константы
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
WIN_SCORE = 150  # Очки для победы

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)  # Цвет для победного сообщения

# Загрузка звуков
try:
    # Проверяем, поддерживается ли звук
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    # Загружаем звук выстрела (замените 'shoot.wav' на ваш файл)
    shoot_sound = pygame.mixer.Sound('pistolet.mp3')
    shoot_sound.set_volume(1.0)  # Устанавливаем громкость (от 0.0 до 1.0)

    # Звук попадания (опционально)
    hit_sound = pygame.mixer.Sound('hit.wav')
    hit_sound.set_volume(0.3)

    # Звук смерти врага (опционально)
    enemy_death_sound = pygame.mixer.Sound('enemy_death.wav')
    enemy_death_sound.set_volume(0.3)

    # Звук получения урона (опционально)
    damage_sound = pygame.mixer.Sound('damage.wav')
    damage_sound.set_volume(0.3)

    # Звук победы (опционально)
    win_sound = pygame.mixer.Sound('win.wav')
    win_sound.set_volume(0.5)

    # Звук проигрыша (опционально)
    game_over_sound = pygame.mixer.Sound('game_over.wav')
    game_over_sound.set_volume(0.5)

    SOUNDS_LOADED = True
except:
    print("Внимание: Не удалось загрузить звуковые файлы. Игра будет без звука.")
    SOUNDS_LOADED = False


    # Создаем заглушки для звуков, чтобы избежать ошибок
    class DummySound:
        def play(self): pass

        def set_volume(self, vol): pass


    shoot_sound = hit_sound = enemy_death_sound = damage_sound = win_sound = game_over_sound = DummySound()


class Wall(pygame.sprite.Sprite):
    """Класс стены"""

    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Player(pygame.sprite.Sprite):
    """Класс игрока"""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([30, 30])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 5
        self.health = 100
        self.max_health = 100

    def update(self, walls):
        """Обновление позиции игрока"""
        keys = pygame.key.get_pressed()
        old_x, old_y = self.rect.x, self.rect.y

        # Движение
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

        # Проверка столкновения со стенами
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x, self.rect.y = old_x, old_y

        # Ограничение движения в пределах экрана
        self.rect.x = max(0, min(self.rect.x, WINDOW_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, WINDOW_HEIGHT - self.rect.height))

    def draw_health_bar(self, screen):
        """Отрисовка полоски здоровья"""
        bar_width = 50
        bar_height = 7
        health_percentage = self.health / self.max_health
        fill = bar_width * health_percentage

        outline_rect = pygame.Rect(self.rect.x - 10, self.rect.y - 15, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - 10, self.rect.y - 15, fill, bar_height)

        pygame.draw.rect(screen, RED, fill_rect)
        pygame.draw.rect(screen, WHITE, outline_rect, 2)


class Enemy(pygame.sprite.Sprite):
    """Класс врага"""

    def __init__(self, x, y, walls, player):
        super().__init__()
        self.image = pygame.Surface([25, 25])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.walls = walls
        self.player = player
        self.health = 50
        self.max_health = 50
        self.damage = 10
        self.shoot_cooldown = 0
        self.shoot_delay = 60  # Задержка между выстрелами (в кадрах)

    def update(self, bullets, enemies):
        """Обновление врага"""
        # Простой ИИ: движение к игроку
        old_x, old_y = self.rect.x, self.rect.y

        # Расчет направления к игроку
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 0:
            dx = dx / distance * self.speed
            dy = dy / distance * self.speed

        self.rect.x += dx
        self.rect.y += dy

        # Проверка столкновения со стенами
        if pygame.sprite.spritecollide(self, self.walls, False):
            self.rect.x, self.rect.y = old_x, old_y

        # Стрельба
        self.shoot_cooldown += 1
        if self.shoot_cooldown >= self.shoot_delay and distance < 300:
            self.shoot(bullets)
            self.shoot_cooldown = 0

    def shoot(self, bullets):
        """Стрельба врага"""
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 0:
            dx = dx / distance * 5
            dy = dy / distance * 5
            bullet = EnemyBullet(self.rect.centerx, self.rect.centery, dx, dy)
            bullets.add(bullet)


class Bullet(pygame.sprite.Sprite):
    """Класс пули игрока"""

    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface([5, 5])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        # Расчет направления
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 0:
            self.speed_x = dx / distance * 10
            self.speed_y = dy / distance * 10
        else:
            self.speed_x = 0
            self.speed_y = 0

    def update(self, walls):
        # Сохраняем старую позицию
        old_x, old_y = self.rect.x, self.rect.y

        """Обновление позиции пули"""
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Проверка столкновения со стенами
        if pygame.sprite.spritecollide(self, walls, False):
            self.kill()  # Уничтожаем пулю при попадании в стену
            return

        # Удаление пули за пределами экрана
        if (self.rect.x < 0 or self.rect.x > WINDOW_WIDTH or
                self.rect.y < 0 or self.rect.y > WINDOW_HEIGHT):
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    """Класс пули врага"""

    def __init__(self, x, y, speed_x, speed_y):
        super().__init__()
        self.image = pygame.Surface([5, 5])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed_x = speed_x
        self.speed_y = speed_y

    def update(self, walls):
        """Обновление позиции пули"""
        # Сохраняем старую позицию
        old_x, old_y = self.rect.x, self.rect.y

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Проверка столкновения со стенами
        if pygame.sprite.spritecollide(self, walls, False):
            self.kill()  # Уничтожаем пулю при попадании в стену
            return

        # Удаление пули за пределами экрана
        if (self.rect.x < 0 or self.rect.x > WINDOW_WIDTH or
                self.rect.y < 0 or self.rect.y > WINDOW_HEIGHT):
            self.kill()


class Game:
    """Основной класс игры"""

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Шутер на Pygame")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)  # Большой шрифт для победного сообщения

        # Группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

        # Создание стен
        self.create_walls()

        # Создание игрока
        self.player = Player(500, 250)
        self.all_sprites.add(self.player)

        # Создание врагов
        for i in range(3):
            self.spawn_enemy()

        self.score = 0
        self.game_over = False
        self.game_won = False  # Новый флаг для отслеживания победы

    def create_walls(self):
        """Создание стен на карте"""
        # Внешние стены (границы карты)
        walls_positions = [
            (0, 0, WINDOW_WIDTH, 10),  # Верхняя стена
            (0, 0, 10, WINDOW_HEIGHT),  # Левая стена
            (WINDOW_WIDTH - 10, 0, 10, WINDOW_HEIGHT),  # Правая стена
            (0, WINDOW_HEIGHT - 10, WINDOW_WIDTH, 10),  # Нижняя стена
        ]

        # Внутренние стены
        inner_walls = [
            (200, 150, 20, 300),
            (400, 200, 20, 200),
            (600, 150, 20, 300),
            (300, 400, 200, 20),
        ]

        for wall_pos in walls_positions + inner_walls:
            wall = Wall(*wall_pos)
            self.walls.add(wall)
            self.all_sprites.add(wall)

    def spawn_enemy(self):
        """Создание нового врага"""
        while True:
            x = random.randint(50, WINDOW_WIDTH - 50)
            y = random.randint(50, WINDOW_HEIGHT - 50)
            enemy = Enemy(x, y, self.walls, self.player)

            # Проверка, что враг не появляется в стене или рядом с игроком
            if not pygame.sprite.spritecollide(enemy, self.walls, False):
                if math.sqrt((x - self.player.rect.x) ** 2 + (y - self.player.rect.y) ** 2) > 100:
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
                    break

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE and not self.game_over and not self.game_won:
                    self.shoot()
                if event.key == pygame.K_r and (self.game_over or self.game_won):
                    self.restart()
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and not self.game_won:
                if event.button == 1:  # Левая кнопка мыши
                    self.shoot()

    def shoot(self):
        """Стрельба игрока"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        bullet = Bullet(self.player.rect.centerx, self.player.rect.centery, mouse_x, mouse_y)
        self.player_bullets.add(bullet)
        self.all_sprites.add(bullet)

    def update(self):
        """Обновление игры"""
        if not self.game_over and not self.game_won:
            # Обновление игрока
            self.player.update(self.walls)

            # Обновление врагов
            for enemy in self.enemies:
                enemy.update(self.enemy_bullets, self.enemies)

            # Обновление пуль с проверкой стен
            for bullet in self.player_bullets:
                bullet.update(self.walls)  # Передаем стены для проверки

            for bullet in self.enemy_bullets:
                bullet.update(self.walls)  # Передаем стены для проверки

            # Проверка попаданий пуль игрока во врагов
            hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, True)
            for enemy in hits:
                enemy.health -= 25
                if enemy.health <= 0:
                    enemy.kill()
                    self.score += 10
                    self.spawn_enemy()

            # Проверка достижения победного счета
            if self.score >= WIN_SCORE:
                self.game_won = True

            # Проверка попаданий пуль врагов в игрока
            hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
            if hits:
                self.player.health -= 10

            # Проверка столкновения игрока с врагами
            hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
            if hits:
                self.player.health -= 1

            # Проверка смерти игрока
            if self.player.health <= 0:
                self.game_over = True

    def draw(self):
        """Отрисовка игры"""
        self.screen.fill(BLACK)

        # Отрисовка всех спрайтов
        self.all_sprites.draw(self.screen)
        self.enemy_bullets.draw(self.screen)

        # Отрисовка полоски здоровья игрока
        self.player.draw_health_bar(self.screen)

        # Отрисовка счета
        score_text = self.font.render(f"Счет: {self.score}/{WIN_SCORE}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Отрисовка количества врагов
        enemies_text = self.font.render(f"Враги: {len(self.enemies)}", True, WHITE)
        self.screen.blit(enemies_text, (10, 50))

        # Отрисовка Game Over
        if self.game_over:
            game_over_text = self.font.render("GAME OVER - Нажмите R для рестарта", True, RED)
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(game_over_text, text_rect)

        # Отрисовка сообщения о победе
        if self.game_won:
            # Затемнение экрана
            s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 128))
            self.screen.blit(s, (0, 0))

            # Победное сообщение
            win_text = self.big_font.render("YOU WIN!", True, GOLD)
            text_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            self.screen.blit(win_text, text_rect)

            # Информация о счете
            score_win_text = self.font.render(f"Твой счет: {self.score}", True, WHITE)
            score_rect = score_win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
            self.screen.blit(score_win_text, score_rect)

            # Инструкция по рестарту
            restart_text = self.font.render("Нажмите R для рестарта или ESC для выхода", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70))
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def restart(self):
        """Перезапуск игры"""
        self.all_sprites.empty()
        self.walls.empty()
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()

        self.create_walls()
        self.player = Player(500, 250)
        self.all_sprites.add(self.player)

        for i in range(3):
            self.spawn_enemy()

        self.score = 0
        self.game_over = False
        self.game_won = False

    def run(self):
        """Основной игровой цикл"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
