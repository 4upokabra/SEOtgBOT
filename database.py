from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import secrets

Base = declarative_base()

class Channel(Base):
    __tablename__ = 'channels'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String, unique=True)
    title = Column(String)
    username = Column(String)
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.now)
    posts = relationship("Post", back_populates="channel")

class GroupStats(Base):
    __tablename__ = 'group_stats'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(String)
    members_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    text = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    views = Column(Integer, default=0)
    message_id = Column(Integer)  # ID сообщения в канале
    comments = relationship("Comment", back_populates="post")
    links = relationship("Link", back_populates="post")
    channel = relationship("Channel", back_populates="posts")

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    text = Column(String)
    sentiment_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    post = relationship("Post", back_populates="comments")

class Link(Base):
    __tablename__ = 'links'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    original_url = Column(String)
    short_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    post = relationship("Post", back_populates="links")
    clicks = relationship("LinkClick", back_populates="link")

class LinkClick(Base):
    __tablename__ = 'link_clicks'
    
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey('links.id'))
    user_agent = Column(String)
    ip_address = Column(String)
    referrer = Column(String)
    click_time = Column(DateTime, default=datetime.now)
    link = relationship("Link", back_populates="clicks")

class Database:
    def __init__(self):
        self.engine = create_engine('sqlite:///seo_bot.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_channel(self, channel_id, title, username):
        channel = Channel(
            channel_id=channel_id,
            title=title,
            username=username
        )
        self.session.add(channel)
        self.session.commit()
        return channel.id

    def get_channel(self, channel_id):
        return self.session.query(Channel).filter(Channel.channel_id == channel_id).first()

    def get_active_channels(self):
        return self.session.query(Channel).filter(Channel.is_active == True).all()

    def update_channel_status(self, channel_id, is_active):
        channel = self.get_channel(channel_id)
        if channel:
            channel.is_active = is_active
            self.session.commit()
            return True
        return False

    def save_members_count(self, group_id, members_count, timestamp):
        stats = GroupStats(
            group_id=group_id,
            members_count=members_count,
            timestamp=timestamp
        )
        self.session.add(stats)
        self.session.commit()

    def save_post(self, text, timestamp, channel_id=None, message_id=None):
        post = Post(
            text=text,
            timestamp=timestamp,
            channel_id=channel_id,
            message_id=message_id
        )
        self.session.add(post)
        self.session.commit()
        return post.id

    def update_post_views(self, message_id, views):
        post = self.session.query(Post).filter(Post.message_id == message_id).first()
        if post:
            post.views = views
            self.session.commit()
            return True
        return False

    def get_channel_posts(self, channel_id, limit=10):
        return self.session.query(Post)\
            .filter(Post.channel_id == channel_id)\
            .order_by(Post.timestamp.desc())\
            .limit(limit)\
            .all()

    def get_channel_statistics(self, channel_id, days=30):
        channel = self.get_channel(channel_id)
        if not channel:
            return None

        # Получаем посты за последние N дней
        start_date = datetime.now() - timedelta(days=days)
        posts = self.session.query(Post)\
            .filter(Post.channel_id == channel.id)\
            .filter(Post.timestamp >= start_date)\
            .order_by(Post.timestamp.desc())\
            .all()

        # Базовая статистика
        total_views = sum(post.views for post in posts)
        total_posts = len(posts)
        avg_views = total_views / total_posts if total_posts > 0 else 0

        # Статистика по дням
        daily_stats = {}
        for post in posts:
            day = post.timestamp.date()
            if day not in daily_stats:
                daily_stats[day] = {'posts': 0, 'views': 0}
            daily_stats[day]['posts'] += 1
            daily_stats[day]['views'] += post.views

        # Топ постов
        top_posts = sorted(posts, key=lambda x: x.views, reverse=True)[:5]

        # Статистика по времени публикации
        hour_stats = {i: 0 for i in range(24)}
        for post in posts:
            hour_stats[post.timestamp.hour] += 1

        # Находим лучшее время для постинга
        best_hour = max(hour_stats.items(), key=lambda x: x[1])[0]

        return {
            'channel_title': channel.title,
            'username': channel.username,
            'total_posts': total_posts,
            'total_views': total_views,
            'average_views': avg_views,
            'last_post_date': posts[0].timestamp if posts else None,
            'daily_stats': daily_stats,
            'top_posts': [
                {
                    'text': post.text[:100] + '...' if len(post.text) > 100 else post.text,
                    'views': post.views,
                    'date': post.timestamp
                } for post in top_posts
            ],
            'hour_stats': hour_stats,
            'best_posting_hour': best_hour,
            'period_days': days
        }

    def get_channel_link_statistics(self, channel_id):
        channel = self.get_channel(channel_id)
        if not channel:
            return None

        # Получаем все посты канала
        posts = self.session.query(Post).filter(Post.channel_id == channel.id).all()
        
        # Собираем статистику по ссылкам
        link_stats = []
        for post in posts:
            links = self.session.query(Link).filter(Link.post_id == post.id).all()
            for link in links:
                clicks = self.session.query(LinkClick).filter(LinkClick.link_id == link.id).all()
                link_stats.append({
                    'original_url': link.original_url,
                    'clicks': len(clicks),
                    'unique_ips': len(set(click.ip_address for click in clicks)),
                    'post_date': post.timestamp,
                    'post_text': post.text[:100] + '...' if len(post.text) > 100 else post.text
                })

        # Сортируем по количеству кликов
        link_stats.sort(key=lambda x: x['clicks'], reverse=True)
        
        return {
            'channel_title': channel.title,
            'total_links': len(link_stats),
            'total_clicks': sum(stat['clicks'] for stat in link_stats),
            'top_links': link_stats[:5]  # Топ-5 ссылок
        }

    def save_comment(self, post_id, text, sentiment_score):
        comment = Comment(
            post_id=post_id,
            text=text,
            sentiment_score=sentiment_score
        )
        self.session.add(comment)
        self.session.commit()

    def create_short_link(self, post_id, original_url):
        # Генерируем уникальный короткий идентификатор
        short_id = secrets.token_urlsafe(6)
        
        link = Link(
            post_id=post_id,
            original_url=original_url,
            short_id=short_id
        )
        self.session.add(link)
        self.session.commit()
        return short_id

    def get_link_by_short_id(self, short_id):
        link = self.session.query(Link).filter(Link.short_id == short_id).first()
        if link:
            return {
                'original_url': link.original_url,
                'post_id': link.post_id
            }
        return None

    def save_link_click(self, original_url, short_url, post_id, user_agent, ip_address, referrer):
        link = self.session.query(Link).filter(Link.original_url == original_url).first()
        if link:
            click = LinkClick(
                link_id=link.id,
                user_agent=user_agent,
                ip_address=ip_address,
                referrer=referrer
            )
            self.session.add(click)
            self.session.commit()

    def get_link_statistics(self, post_id):
        links = self.session.query(Link).filter(Link.post_id == post_id).all()
        stats = []
        for link in links:
            clicks = self.session.query(LinkClick).filter(LinkClick.link_id == link.id).all()
            stats.append({
                'original_url': link.original_url,
                'short_id': link.short_id,
                'clicks': len(clicks),
                'unique_ips': len(set(click.ip_address for click in clicks)),
                'referrers': [click.referrer for click in clicks]
            })
        return stats

    def get_statistics(self):
        # Получаем последние 24 часа статистики
        recent_stats = self.session.query(GroupStats)\
            .filter(GroupStats.timestamp >= datetime.now() - timedelta(days=1))\
            .all()
        
        stats_text = "Статистика за последние 24 часа:\n"
        for stat in recent_stats:
            stats_text += f"Группа {stat.group_id}: {stat.members_count} участников\n"
        
        return stats_text

    def get_recent_comments(self, hours=24):
        return self.session.query(Comment)\
            .filter(Comment.timestamp >= datetime.now() - timedelta(hours=hours))\
            .all() 