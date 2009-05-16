#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import re
import time
import xmpp
from collections import defaultdict
from random import randint as rand
from math import ceil as ceiling
from quinoa import Bot

def owod(dice, diff, spec=False, will=False):
    def norm_roll(dice):
        return sorted(rand(1, 10) for x in xrange(dice))
    def spec_roll(dice):
        rolls = norm_roll(dice)
        tens = rolls.count(10)
        if tens:
            rolls.extend(spec_roll(tens))
        return rolls
    if spec:
        ret = spec_roll(dice)
    else:
        ret = norm_roll(dice)
    ones = 0
    for x in ret:
        if x == 1:
            ones += 1
        if x == 10:
            break
    ret.sort()
    succs = sum(x >= diff for x in ret)
    if will:
        succs += 1
    if not succs and ones:
        succs = 'Botch!'
    else:
        succs = max(0, succs - ones)
    return "%s (%s)" % (succs, ', '.join(map(str, ret)))

def exalted(dice):
    pool = sorted(rand(1, 10) for x in xrange(dice))
    succs = sum(x >= 7 for x in pool)
    ones = pool.count(1)
    if not succs and ones:
        return "Botch (x%s)" % ones
    if not succs and not ones:
        return "Failure."
    return "%s successes." % succs

def btvs(skill):
    rollage = skill + rand(1, 10)
    if rollage <= 8:
        ret = 0
    elif 9 <= rollage <= 16:
        ret = int(ceiling((rollage - 8) / 2.))
    elif 17 <= rollage <= 20:
        ret = 5
    elif 21 <= rollage:
        ret = int(ceiling((rollage - 20) / 3.)) + 5
    return "%s (Total: %s)" % (ret, rollage)

def allflesh(skill):
    die = rand(1, 10)
    more = die
    rol = []
    if die == 10:
        while die == 10:
            nextroll = rand(1, 10)
            rol.append(nextroll)
            additional = max(0, nextroll - 5)
            die = nextroll
            more += additional
    if die == 1:
        while die == 1:
            nextroll = rand(1, 10)
            rol.append(nextroll)
            additional = min(nextroll - 5, 0)
            if additional < 0 and more == die:
                more -= 1
            if nextroll == 1:
                additional -= 1
            die = nextroll
            more += additional
    rollage = skill + more
    if rollage <= 8:
        ret = 0
    elif 9 <= rollage <= 16:
        ret = int(ceiling((rollage - 8) / 2.))
    elif 17 <= rollage <= 20:
        ret = 5
    elif 21 <= rollage:
        ret = int(ceiling((rollage - 20) / 3.)) + 5
    if rol:
        return "%s (Total: %s, role of luck %s)" % \
                (ret, rollage, ', '.join(str(x) for x in rol))
    return "%s (Total: %s)" % (ret, rollage)

def qin():
    yin = rand(1, 10)
    yang = rand(1, 10)
    ret = abs(yin - yang)
    if yin > yang:
        kind = 'yin'
    elif yang > yin:
        kind = 'yang'
    else:
        kind = 'balanced'
    return "%s (%s)" % (ret, kind)

def ork(dice):
    res = defaultdict(int)
    for i in xrange(dice):
        res[rand(1, 6)] += 1
    vals = []
    for k, v in res.items():
        vals.append(v + k - 1)
    vals.sort()
    vals.reverse()
    return ', '.join(map(str, vals))

def wushu(dice, trait):
    return "%s" % sum(x <= trait for x in (rand(1, 6) for y in xrange(dice)))

def alternity(skill, situation):
    if not (-5 < situation < 7):
        return "Situation step out of range"
    control = rand(1, 20)
    dice = {
        -5: lambda: -rand(1, 20),
        -4: lambda: -rand(1, 12),
        -3: lambda: -rand(1, 8),
        -2: lambda: -rand(1, 6),
        -1: lambda: -rand(1, 4),
         0: lambda: 0,
         1: lambda: rand(1, 4),
         2: lambda: rand(1, 6),
         3: lambda: rand(1, 8),
         4: lambda: rand(1, 12),
         5: lambda: rand(1, 20),
         6: lambda: rand(1, 20) + rand(1, 20),
         7: lambda: rand(1, 20) + rand(1, 20) + rand(1, 20),
    }
    if control == 20:
        return "Critical Failure!"
    control += dice[situation]()
    if control > skill:
        ret = "Failure (%s)" % control
    if control <= skill:
        ret = "Ordinary (%s)" % control
    if control <= skill / 2:
        ret = "Good (%s)" % control
    if control <= skill / 4:
        ret = "Amazing (%s)" % control
    return ret

def in_nomine(skill):
    res = rand(1, 6) + rand(1, 6)
    check = rand(1, 6)
    if res + check == 3:
        return "Divine intervention!"
    if res + check == 18:
        return "Infernal intervention!"
    if res <= skill:
        return "Success. (%s)" % check
    return "Failure. (%s)" % check

def pendragon(skill, modifiers):
    res = rand(1, 20)
    if skill + modifiers == res:
        return "Critical success! (%s)" % res
    if res == 20:
        return "Fumble! (%s)" % res
    if res < skill + modifiers:
        return "Success (%s)" % res
    return "Failure (%s)" % res

def shadowrun(pool, leftover, ro6):
    dice = [rand(1, 6) for i in xrange(pool)]
    if ro6:
        sixes = dice.count(6)
        while sixes:
            more_dice = [rand(1, 6) for i in xrange(sixes)]
            sixes = more_dice.count(6)
            dice.extend(more_dice)
    dice.extend([7 for i in xrange(leftover)])
    glitch = dice.count(1) > (len(dice) / 2.)
    successes = sum(x >= 5 for x in dice)
    if glitch and not successes:
        return "Critical glitch! (%s)" % \
            ', '.join([str(x) for x in sorted(dice)])
    if glitch:
        return "%s hits and a glitch. (%s)" % \
            (successes, ', '.join([str(x) for x in sorted(dice)]))
    return "%s hits. (%s)" % \
        (successes, ', '.join([str(x) for x in sorted(dice)]))

def hande(heaven, earth, passing_grade=1):
    pool = [rand(1, 10) for i in range(heaven)]
    num_rerolls_used = 0
    if earth < 0:
        while num_rerolls_used < abs(earth):
            for i, v in enumerate(pool):
                if v >= 7:
                    pool[i] = rand(1, 10)
                    num_rerolls_used += 1
                    break
            if not sum(v >= 7 for v in pool):
                break
    else:
        while num_rerolls_used < earth:
            for i, v in enumerate(pool):
                if v < 7:
                    pool[i] = rand(1, 10)
                    num_rerolls_used += 1
                    break
            if not sum(v < 7 for v in pool):
                break
    hits = sum(x >= 7 for x in pool) + pool.count(10)
    if hits >= passing_grade:
        ret = "Success %d (%s)" % \
                (hits + 1 - passing_grade, ', '.join(str(x) for x in pool))
    else:
        ret = "Failure %d (%s)" % \
                (passing_grade - hits, ', '.join(str(x) for x in pool))
    if num_rerolls_used < abs(earth):
        val = abs(earth) - num_rerolls_used
        ret += " (%d reroll" % val
        if val != 1:
            ret += "s"
        ret += " left)"
    return ret

def generic(num, size):
    return ', '.join(map(str, (rand(1, size) for x in xrange(num))))

class DiceBot(Bot):
    def on_connect(self):
        join = xmpp.protocol.Message()
        join.setBody('join ooc@rooms.transneptune.net')
        self.join(join)
    def register_commands(self):
        self.commands[r'mode\b'] = self.mode
        self.commands[r'roll\b'] = self.roll
        self.commands[r'init\b'] = self.initiative
        self.commands[r'(?i)%s' % '|'.join(MEMES)] = self.meme
    def mode(self, msg):
        """Set or view the bot's current game mode.
            * mode
                shows current mode
            * mode list
                shows possible modes
            * mode <value>
                if <value> in possible modes, sets mode to that value."""
        modes = set([
                "owod",
                "exalted",
                "btvs",
                "allflesh",
                "qin",
                "orkworld",
                "wushu",
                "alternity",
                "innomine",
                "pendragon",
                "shadowrun",
                "h+e"
                ])
        args = msg.getBody()
        try:
            cmd, args = args.split(None, 1)
        except:
            return self.mode
        if args == 'list':
            return ', '.join(sorted(modes))
        if args in modes:
            self.mode = args
            return "Mode set: %s" % args
        return "No such mode."
    def roll(self, msg):
        """There are a number of ways to roll dice.  In all cases, replace # with one or more numerals, and all elements in parentheses are optional:
            * oWoD: roll # at # (s) (w)
                pool size, difficulty, (specialized?) (willpower spent?)
            * Exalted: roll #
                pool size
            * Buffy the Vampire Slayer: roll #
                skill
            * All Flesh Must Be Eaten: roll #
                skill
            * Qin: roll
            * Orkworld: roll #
                pool size
            * Wushu: roll # over #
                pool size, trait
            * Alternity: roll #, (-)#
                skill, (negative) step modifier
            * In Nomine: roll #
                skill
            * Pendragon: roll # (-)#
                skill, modifiers
            * Shadowrun: roll # (#) (s)
                pool, successes from the last roll, (rule of six?)
            * Heaven and Earth: roll # (-)# (#)
                heaven, earth, passing grade
            * Generic Dice: roll #d#
                number, size"""
        args = msg.getBody()
        try:
            command, args = args.split(None, 1)
        except:
            pass
        _generic = re.compile(r'(\d*)d(\d+)')
        _rick = re.compile(r'rick')
        if self.mode == "owod":
            _owod = re.compile(r'^(\d+) at (\d+)( s)?( w)?$')
            if _owod.search(args):
                dice, diff, spec, will = _owod.search(args).groups()
                try:
                    dice = int(dice)
                    diff = int(diff)
                except ValueError, e:
                    return "Bad value: %s" % e
                return owod(dice, diff, spec, will)
        if self.mode == "exalted":
            _exalted = re.compile(r'^(\d+)$')
            if _exalted.search(args):
                dice, = _exalted.search(args).groups()
                try:
                    dice = int(dice)
                except ValueError, e:
                    return "Bad value: %s" % e
                return exalted(dice)
        if self.mode == "btvs":
            _btvs = re.compile(r'^(\d+)$')
            if _btvs.search(args):
                skill, = _btvs.search(args).groups()
                try:
                    skill = int(skill)
                except ValueError, e:
                    return "Bad value: %s" % e
                return btvs(skill)
        if self.mode == "allflesh":
            _allflesh = re.compile(r'^(\d+)$')
            if _allflesh.search(args):
                skill, = _allflesh.search(args).groups()
                try:
                    skill = int(skill)
                except ValueError, e:
                    return "Bad value: %s" % e
                return allflesh(skill)
        if self.mode == "qin":
            _qin = re.compile(r'^$')
            if _qin.search(args):
                return qin()
        if self.mode == "ork":
            _ork = re.compile(r'^(\d+)$')
            if _ork.search(args):
                dice, = _ork.search(args).groups()
                try:
                    dice = int(dice)
                except ValueError, e:
                    return "Bad value: %s" % e
                return ork(int(dice))
        if self.mode == "wushu":
            _wushu = re.compile(r'^(\d+) over (\d+)$')
            if _wushu.search(args):
                dice, trait = _wushu.search(args).groups()
                try:
                    dice = int(dice)
                    trait = int(dice)
                except ValueError, e:
                    return "Bad value: %s" % e
                return wushu(dice, trait)
        if self.mode == "alternity":
            _alternity = re.compile(r'^(\d+), (-?\d+)$')
            if _alternity.search(args):
                skill, situation = _alternity.search(args).groups()
                try:
                    skill = int(skill)
                    situation = int(situation)
                except ValueError, e:
                    return "Bad value: %s" % e
                return alternity(skill, situation)
        if self.mode == "innomine":
            _in_nomine = re.compile(r'^(\d+)$')
            if _in_nomine.search(args):
                skill, = _in_nomine.search(args).groups()
                try:
                    skill = int(skill)
                except ValueError, e:
                    return "Bad value: %s" % e
                return in_nomine(skill)
        if self.mode == "pendragon":
            _pendragon = re.compile(r'^(\d+) (-?\d+)$')
            if _pendragon.search(args):
                skill, modifiers = _pendragon.search(args).groups()
                try:
                    skill = int(skill)
                    modifiers = int(modifiers)
                except ValueError, e:
                    return "Bad value: %s" % e
                return pendragon(skill, modifiers)
        if self.mode == "shadowrun":
            _shadowrun = re.compile(r'^(\d+)( \d+)?( s)?$')
            if _shadowrun.search(args):
                pool, leftover, ro6 = _shadowrun.search(args).groups()
                try:
                    pool = int(pool)
                    if leftover:
                        leftover = int(leftover.strip())
                    else:
                        leftover = 0
                except ValueError, e:
                    return "Bad value: %s" % e
                return shadowrun(pool, leftover, ro6)
        if self.mode == "h+e":
            _hande = re.compile(r'^(\d+) (-?\d+)( \d+)?$')
            if _hande.search(args):
                heaven, earth, passing_grade = _hande.search(args).groups()
                try:
                    heaven = int(heaven)
                    earth = int(earth)
                    if passing_grade:
                        passing_grade = int(passing_grade)
                    else:
                        passing_grade = 1
                except ValueError, e:
                    return "Bad value: %s" % e
                return hande(heaven, earth, passing_grade)
        if _generic.search(args):
            num, size = _generic.search(args).groups()
            if num == '':
                num = 1
            try:
                num = int(num)
                size = int(size)
            except ValueError, e:
                return "Bad size: %s" % e
            return generic(num, size)
        if _rick.search(args):
            time.sleep(rand(1, 3))
            return "http://tinyurl.com/2msmwl"
    def initiative(self, msg):
        """Roll initiative.
        * oWoD: init (name:value)*
        * Shadowrun: init (name:value)*"""
        args = msg.getBody()
        command, args = args.split(None, 1)
        if self.mode == "owod":
            _owod = re.compile(r'^(\w+:\d+)( \w+:\d+)*$')
            if _owod.search(args):
                actors = {}
                elts = args.split()
                for e in elts:
                    k, v = e.split(':')
                    actors[k] = int(v)
                for k, v in actors.items():
                    actors[k] = (rand(1, 10) + v, v)
                return ', '.join(map(lambda x: "%s: %s (%s)" % \
                        (x[0], x[1][0], x[1][1]), \
                        reversed(sorted(actors.items(), \
                                 key=lambda (k, v): (v, k)))))
        if self.mode == "shadowrun":
            _shadowrun = re.compile(r'^(\w+:\d+)( \w+:\d+)*$')
            def shadowrun_sort(a, b):
                a, a2 = a
                b, b2 = b
                anum, atxt = re.search(r'^(\d+)(\w+)?$', a).groups()
                bnum, btxt = re.search(r'^(\d+)(\w+)?$', b).groups()
                ret = cmp(int(anum), int(bnum))
                if ret == 0:
                    ret = -cmp(atxt, btxt)
                if ret == 0:
                    ret = cmp(a2, b2)
                return ret
            if _shadowrun.search(args):
                actors = {}
                elts = args.split()
                for e in elts:
                    k, v = e.split(':')
                    v = int(v)
                    dice = [rand(1, 6) for i in xrange(v)]
                    actors[k] = sum(x >=5 for x in dice)
                    if actors[k] == 0 and dice.count(1) > (len(dice) / 2.):
                        actors[k] = "%scg" % (actors[k] + v)
                    elif actors[k] > 0 and dice.count(1) > (len(dice) / 2.):
                        actors[k] = "%sg" % (actors[k] + v)
                    else:
                        actors[k] = "%s" % (actors[k] + v)
                return ', '.join("%s: %s" % x for x in \
                        reversed(sorted(actors.items(), \
                        key=lambda (k, v): (v, k), cmp=shadowrun_sort)))
        return
    def meme(self, msg):
        args = msg.getBody()
        if rand(1, 30) == 1:
            return "Your mom!"
        if re.search(MEMES[0], args, re.I):
            return "Aaooh! Aaooh! Aaooh!"
        if re.search(MEMES[1], args, re.I):
            return "Fuck all y'all."
        if re.search(MEMES[2], args, re.I):
            return "Stop saying that!"
        if re.search(MEMES[3], args, re.I):
            return "No, it's Doom III."
        if re.search(MEMES[4], args, re.I):
            return "I CAN TELEPORT."
        if re.search(MEMES[5], args, re.I):
            if rand(1, 2) == 1:
                return "ZZ"
            return "RR"
        if re.search(MEMES[6], args, re.I):
            return "You did a barrel roll!"
        if re.search(MEMES[7], args, re.I):
            return "Hahaha… gravity."
        if re.search(MEMES[8], args):
            if rand(1, 10) == 1:
                return "What are you dense? Are you retarded or something?" \
                        " I'm the god damned Batman!"
            return
        if re.search(MEMES[9], args):
            if rand(1, 3) == 1:
                return "What are you dense? Are you retarded or something?" \
                        " I'm the god damned Barman!  I get you beer."
            return
        if re.search(MEMES[10], args, re.I):
            return "I'm not left-handed either."
        if re.search(MEMES[11], args, re.I):
            return "Your mother's lipstick."
        if re.search(MEMES[12], args, re.I):
            return "YA RLY."

MEMES = [r'(spartans(!|,)\s+what is your profession\?)',
        r'(tyche!\s+what is your profession\?)',
        r'((hello(,|\.)\s+)?my name is inigo montoya(,|\.)\s+you killed my father(,|\.)\s+prepare to die(\.|!)?)',
        r'(is this battletoads\?)',
        r"(((what is)|(what's)) celerity (7|seven)\?)",
        r'(do a barrel roll!?)',
        r'(zz$|rr$)',
        r'(i laugh at gravity all the time)',
        r'(.*\bBATMAN\b.*)',
        r'(.*\bBARMAN\b.*)',
        r"(i'm not left( |-)handed(!|\.))",
        r'(what do you have on under (that( kilt)?|there)\?)',
        r'(o rly\??)',
        ]

#~~~~~~~~~~~~~~~~~~~~~~ Run the bot.

if __name__ == "__main__":
    b = DiceBot('test@transneptune.net', 'Tyche', '^^password^^')
    b.mode = "owod"
    b.serve()

