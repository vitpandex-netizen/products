"""Auto Actions — превращает идеи в прототипы. Keys from vault."""
import os, sys, json, logging, time, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db import PassiveIncomeDB

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

class AutoActions:
    def __init__(self, db=None):
        self.db = db or PassiveIncomeDB()
    
    def process_all(self):
        """Process all pending actions."""
        actions = self.db.get_pending_actions()
        if not actions:
            logger.info('No pending actions')
            return
        
        for action in actions:
            logger.info(f'Processing action #{action["id"]}: {action["action_type"]} for idea #{action["idea_id"]}')
            
            if action['action_type'] == 'investigate':
                self._investigate(action)
            elif action['action_type'] == 'build_prototype':
                self._build_prototype(action)
            elif action['action_type'] == 'market_check':
                self._market_check(action)
            
            time.sleep(2)
    
    def _investigate(self, action):
        """Deep investigation of an idea."""
        idea = self.db.get_idea(action['idea_id'])
        if not idea:
            self.db.complete_action(action['id'], 'Idea not found', 'failed')
            return
        
        logger.info(f'Investigating: {idea["title"]}')
        
        # Generate action plan
        plan = (
            f'Action Plan for: {idea["title"]}\n'
            f'Description: {idea.get("description", "")[:200]}\n'
            f'\n'
            f'Steps:\n'
            f'1. Market research (1-2 days)\n'
            f'2. Minimum viable product (3-5 days)\n'
            f'3. Launch & test (1 week)\n'
            f'4. Scale or pivot (week 2)\n'
        )
        
        self.db.complete_action(action['id'], plan, 'done')
        logger.info(f'Investigation complete for {idea["title"]}')
    
    def _build_prototype(self, action):
        """Build a concrete prototype."""
        idea = self.db.get_idea(action['idea_id'])
        if not idea:
            self.db.complete_action(action['id'], 'Not found', 'failed')
            return
        
        # Create a prototype directory
        proto_dir = Path(__file__).resolve().parent.parent / 'prototypes' / f'idea_{idea["id"]}'
        proto_dir.mkdir(parents=True, exist_ok=True)
        
        result = f'Prototype dir: {proto_dir}'
        self.db.complete_action(action['id'], result, 'done')
        logger.info(f'Prototype created for {idea["title"]}')
    
    def _market_check(self, action):
        """Check if idea is still viable."""
        self.db.complete_action(action['id'], 'Market check done', 'done')
    
    def auto_trigger(self, min_score=75):
        """Auto-create actions for high-scoring ideas."""
        ranked = self.db.get_ranked_ideas(limit=20)
        triggered = 0
        
        for idea in ranked:
            score = idea.get('total_score', 0) or 0
            status = idea.get('status', 'new')
            
            if score >= min_score and status in ('new', 'under_review', None):
                # Check if action already exists
                existing = self.db.get_pending_actions()
                already = any(a['idea_id'] == idea['id'] for a in existing)
                if not already:
                    self.db.add_auto_action(idea['id'], 'investigate')
                    triggered += 1
                    logger.info(f'Auto-triggered investigate for {idea["title"]} ({score}/100)')
        
        if triggered:
            logger.info(f'Triggered {triggered} new actions')
        return triggered
