import 'package:flutter/material.dart';
import '../editor/canvas/canvas_model.dart';
import 'template_model.dart';

const _emerald = Color(0xFF0B6E4F);
const _emeraldDark = Color(0xFF063D2C);
const _emeraldLight = Color(0xFFE7F2EC);
const _gold = Color(0xFFC9A227);
const _goldLight = Color(0xFFE4C766);
const _cream = Color(0xFFFAF8F3);
const _ink = Color(0xFF1A1D1B);
const _inkSoft = Color(0xFF4B5049);

TextObject _text({
  required double x,
  required double y,
  required double width,
  required double height,
  required String text,
  String fontFamily = 'Inter',
  double fontSize = 24,
  int weight = 600,
  Color color = _ink,
  TextAlign align = TextAlign.left,
  TextDirection dir = TextDirection.ltr,
  double letterSpacing = 0,
  double lineHeight = 1.25,
}) =>
    TextObject(
      x: x,
      y: y,
      width: width,
      height: height,
      text: text,
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontWeightValue: weight,
      color: color,
      textAlign: align,
      textDirection: dir,
      letterSpacing: letterSpacing,
      lineHeight: lineHeight,
    );

ShapeObject _shape({
  required double x,
  required double y,
  required double width,
  required double height,
  ShapeKind kind = ShapeKind.rectangle,
  Color? fill,
  Color? stroke,
  double strokeWidth = 0,
  double radius = 0,
}) =>
    ShapeObject(
      x: x,
      y: y,
      width: width,
      height: height,
      shapeKind: kind,
      fillColor: fill,
      strokeColor: stroke,
      strokeWidth: strokeWidth,
      cornerRadius: radius,
    );

IconObjectData _icon({
  required double x,
  required double y,
  required double size,
  required String key,
  Color color = _emerald,
}) =>
    IconObjectData(x: x, y: y, width: size, height: size, iconKey: key, color: color);

/// TASMIM's built-in template library. Deliberately scoped per the
/// Feature Prioritization Framework's Tier A: a small, genuinely good set
/// spanning general use and the Islamic Suite wedge — not an attempt at
/// Canva-scale breadth.
class TemplateLibrary {
  TemplateLibrary._();

  static final List<DesignTemplate> all = [
    _saleAnnouncement,
    _corporateUpdate,
    _ramadanIftarInvitation,
    _eidMubarakGreeting,
    _fridayLectureSeries,
    _communityIftarNight,
    _dailyReminderQuote,
    _reflectionReminderStory,
  ];

  static List<DesignTemplate> byCategory(TemplateCategory category) =>
      all.where((t) => t.category == category).toList();

  // ---- General ----------------------------------------------------------

  static final _saleAnnouncement = DesignTemplate(
    id: 'general_sale_announcement',
    name: 'Modern Sale Announcement',
    category: TemplateCategory.socialMedia,
    build: () => CanvasDocument(
      title: 'Modern Sale Announcement',
      canvasWidth: CanvasSizePreset.social.width,
      canvasHeight: CanvasSizePreset.social.height,
      backgroundColor: _cream,
      category: 'general',
      objects: [
        _shape(x: 0, y: 760, width: 1080, height: 320, fill: _emerald),
        _shape(x: 0, y: 742, width: 1080, height: 8, fill: _gold),
        _icon(x: 900, y: 70, size: 64, key: 'sparkle', color: _gold),
        _text(
          x: 60,
          y: 260,
          width: 960,
          height: 140,
          text: 'BIG SALE',
          fontFamily: 'Cairo',
          fontSize: 96,
          weight: 800,
          color: _emerald,
          align: TextAlign.center,
        ),
        _text(
          x: 90,
          y: 400,
          width: 900,
          height: 60,
          text: 'Up to 50% off everything',
          fontSize: 32,
          weight: 500,
          color: _inkSoft,
          align: TextAlign.center,
        ),
        _text(
          x: 90,
          y: 850,
          width: 900,
          height: 60,
          text: 'Shop the collection today',
          fontFamily: 'Cairo',
          fontSize: 30,
          weight: 700,
          color: Colors.white,
          align: TextAlign.center,
        ),
      ],
    ),
  );

  static final _corporateUpdate = DesignTemplate(
    id: 'general_corporate_update',
    name: 'Clean Corporate Update',
    category: TemplateCategory.general,
    build: () => CanvasDocument(
      title: 'Clean Corporate Update',
      canvasWidth: CanvasSizePreset.banner.width,
      canvasHeight: CanvasSizePreset.banner.height,
      backgroundColor: _cream,
      category: 'general',
      objects: [
        _shape(x: 0, y: 0, width: 24, height: 900, fill: _emerald),
        _shape(x: 120, y: 460, width: 120, height: 8, fill: _gold),
        _text(
          x: 120,
          y: 300,
          width: 1200,
          height: 100,
          text: 'Quarterly Update',
          fontFamily: 'Cairo',
          fontSize: 64,
          weight: 700,
          color: _ink,
        ),
        _text(
          x: 120,
          y: 500,
          width: 1000,
          height: 50,
          text: 'Q3 2026 performance highlights',
          fontSize: 28,
          weight: 500,
          color: _inkSoft,
        ),
      ],
    ),
  );

  // ---- Islamic Flyers -----------------------------------------------------

  static final _ramadanIftarInvitation = DesignTemplate(
    id: 'islamic_ramadan_iftar',
    name: 'Ramadan Iftar Invitation',
    category: TemplateCategory.islamicFlyer,
    build: () => CanvasDocument(
      title: 'Ramadan Iftar Invitation',
      canvasWidth: CanvasSizePreset.flyer.width,
      canvasHeight: CanvasSizePreset.flyer.height,
      backgroundColor: _cream,
      category: 'islamic-flyer',
      objects: [
        _shape(x: 0, y: 0, width: 1240, height: 420, fill: _emerald),
        _icon(x: 560, y: 55, size: 120, key: 'crescent', color: Colors.white),
        _text(
          x: 0,
          y: 200,
          width: 1240,
          height: 90,
          text: 'دعوة إلى الإفطار',
          fontFamily: 'Amiri',
          fontSize: 60,
          weight: 700,
          color: Colors.white,
          align: TextAlign.center,
          dir: TextDirection.rtl,
        ),
        _text(
          x: 0,
          y: 310,
          width: 1240,
          height: 50,
          text: 'RAMADAN IFTAR INVITATION',
          fontFamily: 'Cairo',
          fontSize: 24,
          weight: 600,
          color: _goldLight,
          align: TextAlign.center,
          letterSpacing: 2,
        ),
        _icon(x: 470, y: 470, size: 300, key: 'ornament_divider', color: _gold),
        _text(
          x: 120,
          y: 560,
          width: 1000,
          height: 90,
          text: 'تفضلوا بالانضمام إلينا لحظة الإفطار في هذا الشهر المبارك',
          fontFamily: 'NotoNaskhArabic',
          fontSize: 32,
          weight: 500,
          color: _ink,
          align: TextAlign.center,
          dir: TextDirection.rtl,
          lineHeight: 1.6,
        ),
        _text(
          x: 120,
          y: 680,
          width: 1000,
          height: 50,
          text: 'Join us for Iftar this blessed month',
          fontSize: 22,
          weight: 400,
          color: _inkSoft,
          align: TextAlign.center,
        ),
        _icon(x: 200, y: 830, size: 44, key: 'calendar', color: _emerald),
        _text(
          x: 260,
          y: 838,
          width: 780,
          height: 40,
          text: 'First Friday of Ramadan',
          fontSize: 26,
          weight: 500,
          color: _ink,
        ),
        _icon(x: 200, y: 900, size: 44, key: 'location', color: _emerald),
        _text(
          x: 260,
          y: 908,
          width: 780,
          height: 40,
          text: 'Main Prayer Hall',
          fontSize: 26,
          weight: 500,
          color: _ink,
        ),
        _icon(x: 200, y: 970, size: 44, key: 'clock', color: _emerald),
        _text(
          x: 260,
          y: 978,
          width: 780,
          height: 40,
          text: 'Right after Maghrib Adhan',
          fontSize: 26,
          weight: 500,
          color: _ink,
        ),
        _shape(x: 0, y: 1600, width: 1240, height: 148, fill: _gold),
        _text(
          x: 0,
          y: 1648,
          width: 1240,
          height: 50,
          text: 'All are welcome',
          fontFamily: 'Cairo',
          fontSize: 30,
          weight: 700,
          color: Colors.white,
          align: TextAlign.center,
        ),
      ],
    ),
  );

  static final _eidMubarakGreeting = DesignTemplate(
    id: 'islamic_eid_mubarak',
    name: 'Eid Mubarak Greeting',
    category: TemplateCategory.islamicFlyer,
    build: () => CanvasDocument(
      title: 'Eid Mubarak Greeting',
      canvasWidth: CanvasSizePreset.social.width,
      canvasHeight: CanvasSizePreset.social.height,
      backgroundColor: _cream,
      category: 'islamic-flyer',
      objects: [
        _shape(x: 140, y: 60, width: 800, height: 800, kind: ShapeKind.circle, fill: _emeraldLight),
        _icon(x: 440, y: 130, size: 200, key: 'crescent', color: _gold),
        _text(
          x: 40,
          y: 380,
          width: 1000,
          height: 150,
          text: 'عيد مبارك',
          fontFamily: 'Amiri',
          fontSize: 110,
          weight: 700,
          color: _emerald,
          align: TextAlign.center,
          dir: TextDirection.rtl,
        ),
        _text(
          x: 40,
          y: 545,
          width: 1000,
          height: 60,
          text: 'EID MUBARAK',
          fontFamily: 'Cairo',
          fontSize: 40,
          weight: 700,
          color: _gold,
          align: TextAlign.center,
          letterSpacing: 4,
        ),
        _icon(x: 390, y: 630, size: 300, key: 'ornament_divider', color: _gold),
        _text(
          x: 90,
          y: 720,
          width: 900,
          height: 80,
          text: 'Wishing you and your family a blessed Eid',
          fontSize: 26,
          weight: 500,
          color: _inkSoft,
          align: TextAlign.center,
        ),
        _icon(x: 60, y: 60, size: 48, key: 'star_eight', color: _gold),
        _icon(x: 972, y: 60, size: 48, key: 'star_eight', color: _gold),
      ],
    ),
  );

  // ---- Mosque Events ------------------------------------------------------

  static final _fridayLectureSeries = DesignTemplate(
    id: 'mosque_friday_lecture',
    name: 'Friday Lecture Series',
    category: TemplateCategory.mosqueEvent,
    build: () => CanvasDocument(
      title: 'Friday Lecture Series',
      canvasWidth: CanvasSizePreset.flyer.width,
      canvasHeight: CanvasSizePreset.flyer.height,
      backgroundColor: _cream,
      category: 'mosque-event',
      objects: [
        _icon(x: 520, y: 60, size: 200, key: 'mosque_dome', color: _emerald),
        _text(
          x: 0,
          y: 300,
          width: 1240,
          height: 70,
          text: 'Friday Lecture Series',
          fontFamily: 'Cairo',
          fontSize: 52,
          weight: 700,
          color: _emerald,
          align: TextAlign.center,
        ),
        _text(
          x: 0,
          y: 380,
          width: 1240,
          height: 60,
          text: 'سلسلة محاضرات الجمعة',
          fontFamily: 'Amiri',
          fontSize: 40,
          weight: 700,
          color: _gold,
          align: TextAlign.center,
          dir: TextDirection.rtl,
        ),
        _shape(x: 120, y: 520, width: 1000, height: 150, kind: ShapeKind.roundedRectangle, fill: _emerald, radius: 24),
        _text(
          x: 160,
          y: 560,
          width: 920,
          height: 40,
          text: 'Speaker',
          fontFamily: 'Cairo',
          fontSize: 20,
          weight: 500,
          color: _goldLight,
        ),
        _text(
          x: 160,
          y: 595,
          width: 920,
          height: 50,
          text: '[Guest Speaker Name]',
          fontSize: 32,
          weight: 700,
          color: Colors.white,
        ),
        _icon(x: 200, y: 740, size: 44, key: 'calendar', color: _emerald),
        _text(x: 260, y: 748, width: 780, height: 40, text: 'Every Friday, after Maghrib', fontSize: 26, weight: 500, color: _ink),
        _icon(x: 200, y: 810, size: 44, key: 'location', color: _emerald),
        _text(x: 260, y: 818, width: 780, height: 40, text: 'Main Hall', fontSize: 26, weight: 500, color: _ink),
        _icon(x: 200, y: 880, size: 44, key: 'people', color: _emerald),
        _text(x: 260, y: 888, width: 780, height: 40, text: 'Open to everyone', fontSize: 26, weight: 500, color: _ink),
        _shape(x: 0, y: 1600, width: 1240, height: 148, fill: _gold),
        _text(x: 0, y: 1648, width: 1240, height: 50, text: 'Everyone Welcome', fontFamily: 'Cairo', fontSize: 30, weight: 700, color: Colors.white, align: TextAlign.center),
      ],
    ),
  );

  static final _communityIftarNight = DesignTemplate(
    id: 'mosque_community_iftar',
    name: 'Community Iftar Night',
    category: TemplateCategory.mosqueEvent,
    build: () => CanvasDocument(
      title: 'Community Iftar Night',
      canvasWidth: CanvasSizePreset.poster.width,
      canvasHeight: CanvasSizePreset.poster.height,
      backgroundColor: _emeraldDark,
      category: 'mosque-event',
      objects: [
        _icon(x: 650, y: 100, size: 200, key: 'lantern', color: _gold),
        _text(x: 0, y: 380, width: 1500, height: 90, text: 'Community Iftar Night', fontFamily: 'Cairo', fontSize: 64, weight: 700, color: Colors.white, align: TextAlign.center),
        _text(x: 0, y: 480, width: 1500, height: 80, text: 'ليلة الإفطار الجماعي', fontFamily: 'Amiri', fontSize: 48, weight: 700, color: _gold, align: TextAlign.center, dir: TextDirection.rtl),
        _icon(x: 650, y: 590, size: 200, key: 'ornament_divider', color: _goldLight),
        _shape(x: 200, y: 1500, width: 1100, height: 420, kind: ShapeKind.roundedRectangle, fill: _cream, radius: 32),
        _icon(x: 260, y: 1560, size: 48, key: 'calendar', color: _emerald),
        _text(x: 330, y: 1568, width: 900, height: 40, text: 'Every evening throughout Ramadan', fontSize: 28, weight: 500, color: _ink),
        _icon(x: 260, y: 1650, size: 48, key: 'location', color: _emerald),
        _text(x: 330, y: 1658, width: 900, height: 40, text: 'Community Hall, behind the mosque', fontSize: 28, weight: 500, color: _ink),
        _icon(x: 260, y: 1740, size: 48, key: 'hand_heart', color: _emerald),
        _text(x: 330, y: 1748, width: 900, height: 40, text: 'Volunteers and donations welcome', fontSize: 28, weight: 500, color: _ink),
        _icon(x: 260, y: 1830, size: 48, key: 'people', color: _emerald),
        _text(x: 330, y: 1838, width: 900, height: 40, text: 'Bring your family and neighbors', fontSize: 28, weight: 500, color: _ink),
      ],
    ),
  );

  // ---- Da'wah Posters -------------------------------------------------------

  static final _dailyReminderQuote = DesignTemplate(
    id: 'dawah_daily_reminder',
    name: 'Daily Reminder Quote',
    category: TemplateCategory.dawahPoster,
    build: () => CanvasDocument(
      title: 'Daily Reminder Quote',
      canvasWidth: CanvasSizePreset.social.width,
      canvasHeight: CanvasSizePreset.social.height,
      backgroundColor: _cream,
      category: 'dawah-poster',
      objects: [
        _icon(x: 490, y: 90, size: 100, key: 'ornament_divider', color: _gold),
        _text(
          x: 100,
          y: 260,
          width: 880,
          height: 220,
          text: 'خير الناس أنفعهم للناس',
          fontFamily: 'NotoNaskhArabic',
          fontSize: 52,
          weight: 700,
          color: _ink,
          align: TextAlign.center,
          dir: TextDirection.rtl,
          lineHeight: 1.5,
        ),
        _text(
          x: 140,
          y: 520,
          width: 800,
          height: 100,
          text: 'The best of people are those who benefit others.',
          fontSize: 24,
          weight: 500,
          color: _inkSoft,
          align: TextAlign.center,
        ),
        _text(
          x: 140,
          y: 640,
          width: 800,
          height: 40,
          text: '— Prophetic Tradition',
          fontFamily: 'Cairo',
          fontSize: 20,
          weight: 600,
          color: _gold,
          align: TextAlign.center,
        ),
        _icon(x: 490, y: 780, size: 100, key: 'ornament_divider', color: _gold),
        _icon(x: 60, y: 960, size: 40, key: 'crescent', color: _emerald),
      ],
    ),
  );

  static final _reflectionReminderStory = DesignTemplate(
    id: 'dawah_reflection_story',
    name: 'Reflection Reminder',
    category: TemplateCategory.dawahPoster,
    build: () => CanvasDocument(
      title: 'Reflection Reminder',
      canvasWidth: CanvasSizePreset.story.width,
      canvasHeight: CanvasSizePreset.story.height,
      backgroundColor: _emerald,
      category: 'dawah-poster',
      objects: [
        _icon(x: 490, y: 140, size: 100, key: 'star_eight', color: _gold),
        _text(
          x: 90,
          y: 320,
          width: 900,
          height: 130,
          text: 'تذكير',
          fontFamily: 'Amiri',
          fontSize: 90,
          weight: 700,
          color: _gold,
          align: TextAlign.center,
          dir: TextDirection.rtl,
        ),
        _text(
          x: 120,
          y: 520,
          width: 840,
          height: 260,
          text: 'من صمت نجا. احفظ لسانك، وأحسن الظن، واجعل قلبك عامرًا بذكر الله',
          fontFamily: 'NotoNaskhArabic',
          fontSize: 36,
          weight: 500,
          color: Colors.white,
          align: TextAlign.center,
          dir: TextDirection.rtl,
          lineHeight: 1.7,
        ),
        _text(
          x: 140,
          y: 840,
          width: 800,
          height: 120,
          text: 'Whoever remains silent is saved. Guard your tongue, think well of others, '
              'and keep your heart alive with the remembrance of Allah.',
          fontSize: 22,
          weight: 400,
          color: _goldLight,
          align: TextAlign.center,
          lineHeight: 1.5,
        ),
        _icon(x: 500, y: 1780, size: 80, key: 'minaret', color: Colors.white),
      ],
    ),
  );
}
