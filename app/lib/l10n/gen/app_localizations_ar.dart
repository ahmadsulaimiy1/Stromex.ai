// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String get appName => 'تصميم';

  @override
  String get appTagline => 'التصميم في أبهى صوره.';

  @override
  String get onboardTitle1 => 'صمّم في ثوانٍ';

  @override
  String get onboardBody1 =>
      'صف ما تحتاجه أو ابدأ من قالب جاهز — يقوم تصميم ببناء مسودة حقيقية وقابلة للتعديل فورًا.';

  @override
  String get onboardTitle2 => 'لوحة تصميم احترافية';

  @override
  String get onboardBody2 =>
      'نصوص، أشكال، أيقونات، طبقات، وتحكم دقيق بالألوان — بلا حدود مهما تقدمت في احترافيتك.';

  @override
  String get onboardTitle3 => 'مصمم للتصميم الإسلامي';

  @override
  String get onboardBody3 =>
      'خط عربي أصيل ومجموعة مخصصة من قوالب المطويات الإسلامية، وفعاليات المساجد، والدعوة.';

  @override
  String get skip => 'تخطي';

  @override
  String get continueLabel => 'متابعة';

  @override
  String get getStarted => 'ابدأ الآن';

  @override
  String get continueWithoutAccount => 'المتابعة بدون حساب';

  @override
  String get createLocalProfile => 'إنشاء ملف تعريف محلي';

  @override
  String get alreadyHaveProfile => 'لدي ملف تعريف بالفعل على هذا الجهاز';

  @override
  String get profileDisclaimer =>
      'تُحفظ الملفات الشخصية بأمان على هذا الجهاز فقط — لا يوجد نظام حسابات سحابي في هذا الإصدار من تصميم.';

  @override
  String get dashboardGreetingGuest => 'أهلًا بك — تصمم كضيف';

  @override
  String dashboardGreetingBack(String name) {
    return 'أهلًا بعودتك، $name';
  }

  @override
  String get whatToCreate => 'ماذا تحب أن تصمم اليوم؟';

  @override
  String get newDesign => 'تصميم جديد';

  @override
  String get aiGenerate => 'إنشاء بالذكاء الاصطناعي';

  @override
  String get templates => 'القوالب';

  @override
  String get inspiration => 'الإلهام';

  @override
  String get recentProjects => 'المشاريع الأخيرة';

  @override
  String get noProjectsTitle => 'لا توجد مشاريع بعد';

  @override
  String get noProjectsMessage =>
      'ابدأ من قالب أو أنشئ تصميمًا بالذكاء الاصطناعي — ستظهر مشاريعك المحفوظة هنا.';

  @override
  String get browseTemplates => 'تصفح القوالب';

  @override
  String get settingsTitle => 'الإعدادات';

  @override
  String get appearance => 'المظهر';

  @override
  String get light => 'فاتح';

  @override
  String get dark => 'داكن';

  @override
  String get systemDefault => 'حسب النظام';

  @override
  String get language => 'اللغة';

  @override
  String get english => 'English';

  @override
  String get arabic => 'العربية';

  @override
  String get aiSection => 'الذكاء الاصطناعي';

  @override
  String get apiKeyLabel => 'مفتاح واجهة Anthropic البرمجية';

  @override
  String get apiKeyConfigured => 'تم الإعداد';

  @override
  String get apiKeyNotSet =>
      'لم يُعدّ بعد — ميزات الذكاء الاصطناعي تحتاج إلى مفتاح';

  @override
  String get accountSection => 'الحساب';

  @override
  String get signOut => 'تسجيل الخروج';

  @override
  String get deleteProfileAction => 'حذف الملف الشخصي';

  @override
  String get diagnostics => 'التشخيص';

  @override
  String get save => 'حفظ';

  @override
  String get export => 'تصدير';

  @override
  String get cancel => 'إلغاء';

  @override
  String get done => 'تم';
}
