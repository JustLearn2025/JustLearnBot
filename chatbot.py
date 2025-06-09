import logging
import os
import json
import pytz
import sys
import hashlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import faiss
import random
from io import BytesIO
from datetime import datetime, time, timedelta
from database.database_manager import DatabaseManager
from typing import Dict, List, Optional, Set, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager('data/justlearn.db')

TEXTS = {
    "en": {
        # Start command and welcome
        "hello": "Hello",
        "welcome_to_bot": "Welcome to JUSTLearn Bot for Computer Science Department.",
        "bot_description": "I can help you practice with MCQs for your exams. Here's how to use me:",
        "commands_header": "Commands",
        "topics_command": "Show all available topics",
        "adaptive_test_command": "Start an adaptive test that adjusts to your skill level",
        "mimic_exam_command": "Start a simulated in-camp exam (First, Second, or Final)",
        "results_command": "Show your last 5 test performances",
        "reset_command": "Cancel current test session",
        "set_reminder_command": "Set up daily test reminders",
        "adaptive_test_description": "The adaptive test will help identify your strengths and weaknesses!",
        "language_selection": "Please select your preferred language:",
        "use_start_command": "🏠 Use /start to access the main menu and explore all bot features!",
        "subjects_command": "Show all available subjects",
        "subjects_header": "📚 Available Subjects:",
        "subjects_description": "Choose a subject to explore its topics and tests:",

        # Contact Us Command
        "contact_us_command": "Contact us for support and suggestions",
        "contact_us_header": "📞 Contact Us",
        "contact_us_message": "If you want to:\n\n• Suggest enhancements\n• Report bugs\n• Offer questions to enhance the question bank\n\nPlease contact us here:\n📧 **just.learn.supp@gmail.com**\n\nWe appreciate your feedback and contributions!",

        # Topics list
        "select_subject": "📚 Select a Subject",

        # Adaptive test session
        "active_session": "❗ You already have an active test session. Complete it first or use /reset to cancel it.",
        "welcome_adaptive": "🧠 Welcome to the Adaptive Evaluation Test!\n\nThis test will help identify your strengths and weaknesses by dynamically adjusting question difficulty.\n\nSelect the topics you want to include (you can select multiple):",
        "session_expired": "⚠️ Your session has expired. Please start again with /adaptive_test",
        "select_topics": "Select topics for your test:",
        "please_select": "⚠️ Please select at least one topic before starting the test.",
        "error_starting": "⚠️ Error starting test. Please try again with /adaptive_test",
        "no_questions": "⚠️ No questions available for {} with Medium difficulty. Please try another topic.",
        "test_started": "🎓 Adaptive Test Started!\n\nStarting with: {}\n\nThe test will adapt based on your answers. Good luck!",
        
        # Question answers
        "correct": "✅ Correct!",
        "incorrect": "❌ Incorrect!\n\nThe correct answer is: {}\n\n📚 Explanation:\n{}",
        "topic_weak": "❗ You seem to struggle with {}. It has been marked as a weak topic.",
        "moving_next": "🔄 Moving to next topic: {}",
        "no_topic_questions": "⚠️ No questions available for {}. Ending test.",
        "completed": "Test completed!",
        "max_reached": "Maximum questions reached for this topic. Moving to next topic.",
        "no_more_questions": "No more questions or topics available. Test completed.",
        
        # Next action messages
        "moving_to_hard": "Moving to a Hard question on the same topic.",
        "moving_to_medium": "Moving to a Medium question on the same topic.",
        "moving_to_easy": "Moving to an Easy question on the same topic.",
        "hard_question_incorrect": "⚠️ You answered the hard question on {} incorrectly.\n\n📚 Suggestion: Review this topic to strengthen your understanding.",
        "topic_complete_success": "You have successfully completed {}. Moving to the next topic.",
        "moving_next_question": "Moving to the next question.",
        
        # Reevaluation test
        "reevaluation_cleared": "⚠️ Your previous test session has been cleared to start a new reevaluation test for {}.\n\nIMPORTANT: Previous test questions are no longer active.",
        "starting_reevaluation": "Starting reevaluation test for {}...",
        "new_reevaluation": "📝 NEW REEVALUATION TEST: {}\n\nThis test consists of questions with varying difficulty levels.\nLet's see if you can improve your understanding!",
        "old_session": "⚠️ This question is from a previous session that is no longer active.\n\nPlease answer only questions from your current active session.",
        "reevaluation_error": "❗ An error occurred while starting the reevaluation test. Please try again or use /reset to clear your session.",
        "reevaluation_skipped": "Reevaluation skipped. You can view your results with /results or start a new test with /adaptive_test.",
        "returning_adaptive": "🔄 Returning to adaptive test. Next topic: {}",
        "reevaluation_completed": "🎓 Reevaluation Test Completed!\n\n{}\nScore: {}\n\n",
        "topic_still_weak": "⚠️ {}: Still weak, needs more review.\n",
        "topic_improved": "✅ {}: Improved! Good job.\n",
        "would_like_reevaluation": "Would you like to take a reevaluation test on '{}'?",
        "reevaluate_topic": "📚 Reevaluate: {}",
        "reevaluation_test": "Reevaluation Test",
        "advanced_reevaluation_test": "Advanced Reevaluation Test",
        "advanced_practice_prompt": "Would you like advanced practice on '{}' to improve your high-level performance?\n\n📚 **Reevaluation Test**: 3 questions (1 Easy, 1 Medium, 1 Hard)\n🔥 **Advanced Reevaluation Test**: 3 Hard level questions for mastery",
        
        # Test completion
        "test_completed": "Adaptive Test Completed!",
        "test_date": "Date: {}",
        "test_score": "Score: {}",
        "topics_tested": "Topics Tested: {}",
        "topics_to_review": "Topics to Review",
        "mastered_topics": "Mastered Topics: {}",
        "topics_needing_advanced_practice": "Topics needing advanced practice",
        "view_results": "View your full performance history with /results",
        "start_another": "Start another adaptive test with /adaptive_test",
        
        # Recommendations
        "recommended_resources": "Recommended Resources",
        "video_tutorial": "Video Tutorial",
        "reading_material": "Reading Material",
        
        # UI buttons
        "select_all": "Select All",
        "clear_all": "Clear All",
        "start_test": "Start Test",
        "select_language": "Select Language / اختر اللغة",
        "language_changed": "Language changed to English",
        "start_adaptive_button": "🧠 Start Adaptive Test",
        "start_mimic_exam_button": "🎯 Start Mimic Exam",
        "return_to_main_menu": "🏠 Return to Main Menu",
        "what_next": "What would you like to do next?",
        
        # Reset command
        "reset_confirmation": "✅ Your session has been completely reset.",
        
        # No explanation fallback
        "no_explanation": "No explanation available.",
        
        # Skip exam details message
        "skip_exam_details": "You've chosen to skip the detailed results.",
        
        # Topics command
        "topics_header": "📚 Available Topics:",
        "topics_reset": "\n\n✅ Your active session has been reset.",
        "topics_empty": "No topics available. Please contact the administrator.",
        "start_adaptive_from_topics": "Start Adaptive Test",
        
        # Results command
        "results_header": "📊 Your Test Results (Last 5):",
        "results_empty": "📊 You haven't taken any tests yet.",
        "results_test_entry": "{index}. {test_type} ({date})\n   Score: {score}\n   Weak Topics: {weak_topics}\n\n",
        "results_weak_topics": "🔍 Your Top Weak Topics: {topics}",
        "results_no_weak_topics": "None",
        
        # Exam completion
        "exam_complete": "✅ Exam Complete!",
        "your_score": "🧾 Your Score: {}",
        "topics_to_review_header": "📉 Topics to Review:",
        "no_detailed_questions": "No detailed questions available for this test.",
        "review_questions_prompt": "Would you like to review the questions and answers?",
        "continue_options": "View your full performance history with /results\nStart another exam with /mimic_incamp_exam",
        "exam_complete_simple": "✅ Exam Complete! Your Score: {}\n\nView your full performance history with /results",
        "show_detailed_button": "Show Detailed Results",
        "show_incorrect_button": "Show Only Incorrect Answers",
        "skip_details_button": "Skip Details",
        "answer_recorded": "Answer {} recorded",
        
        # Mimic exam command
        "mimic_exam_header": "🎯 In-Camp Exam Simulation",
        "mimic_exam_intro": "Choose the exam type you would like to take:",
        "first_exam_desc": "1️⃣ First Exam: Big-O, Arrays, Linked Lists (20 questions)",
        "second_exam_desc": "2️⃣ Second Exam: Stacks, Queues, Recursion, Hashing (20 questions)",
        "final_exam_desc": "3️⃣ Final Exam: All Topics (40 questions)",
        "exam_experience_note": "Each exam mimics the structure and experience of in-camp CS211 exams.",
        
        # First exam
        "first_exam_start": "📝 Starting First Exam: Big-O, Arrays, Linked Lists\n\nThis exam contains 20 questions. Good luck!",
        
        # Second exam
        "second_exam_header": "🧠 Second Exam: Stacks, Queues, Recursion, Hashing",
        "second_exam_topics": "This exam covers Stacks, Queues, Recursion, and optionally Hashing.",
        "second_exam_count": "The exam contains 20 questions in total.",
        "second_exam_option": "Would you like to include or exclude the Hashing topic?",
        "include_hashing": "Include Hashing",
        "exclude_hashing": "Exclude Hashing",
        "second_exam_start": "📝 Starting Second Exam{}.\n\nThis exam contains 20 questions. Good luck!",
        "with_hashing": " with Hashing",
        
        # Final exam
        "final_exam_header": "📝 Final Exam: All Topics",
        "final_exam_topics": "This exam covers all topics from the course.",
        "final_exam_count": "The exam contains 40 questions in total.",
        "final_exam_option": "Would you like to include or exclude the Big-O topic?",
        "include_big_o": "Include Big-O",
        "exclude_big_o": "Exclude Big-O",
        "final_exam_start": "📝 Starting Final Exam{}.\n\nThis exam contains 40 questions. Good luck!",
        "without_big_o": " without Big-O",
        
        # Common exam elements
        "back_to_exam": "Back to Exam Selection",
        "congratulations": "🎉 Congratulations! You had no incorrect answers.",
        
        # Reminder command texts
        "reminder_header": "📅 Daily Test Reminder Settings",
        "reminder_enabled": "✅ Daily reminders are ENABLED",
        "reminder_disabled": "❌ Daily reminders are DISABLED", 
        "reminder_time": "\n🕐 Reminder time: {}",
        "reminder_description": "Stay consistent with your learning! Get daily reminders to practice with tests and improve your performance.",
        "no_reminder_active": "No reminder active",
        "please_select_reminder_time": "⏰ Please select a reminder time:",
        "next_reminder": "Next reminder: {}",
        "today_at": "Today at {}",
        "jordan_time": "(Jordan time)",
        "enable_reminders_first": "❌ Please enable reminders first before setting a time.",

        # Reminder buttons
        "enable_reminder": "🔔 Enable Daily Reminders",
        "disable_reminder": "🔕 Disable Reminders",
        "change_time_morning": "🌅 Morning (9:00)",
        "change_time_afternoon": "☀️ Afternoon (14:00)", 
        "change_time_evening": "🌙 Evening (19:00)",
        "change_time_custom": "⏰ Custom Time",

        # Reminder status messages
        "reminder_turned_on": "✅ Daily reminders have been turned ON!",
        "reminder_turned_off": "❌ Daily reminders have been turned OFF.",
        "reminder_time_updated": "🕐 Reminder time updated to {}",
        "reminder_settings_saved": "Your reminder settings have been saved.",
        "custom_time_instruction": "To set a custom time, please use the 24-hour format: /set_reminder HH:MM\nExample: /set_reminder 08:30 (8:30 AM) or /set_reminder 20:30 (8:30 PM)",
        "notifications_deleted": "🗑️ All pending notifications have been deleted.",

        # Daily reminder message
        "daily_reminder_header": "📚 Daily Learning Reminder!",
        "daily_reminder_footer": "Keep up the great work with your studies! 💪",
        "reminder_weak_topics": "💡 Focus on your weak topics: {}",
        "reminder_general_suggestion": "💡 Practice makes perfect! Try an adaptive test or mimic exam.",
        
        # Progress Command messages
        "progress_no_data": "📊 You haven't completed any quizzes yet. Take a quiz first to see your progress!",
        "progress_need_more": "📊 You need to complete more quizzes to view your progress. Keep practicing!",
        "progress_title": "📈 Your Quiz Progress",
        "progress_total": "📊 Total Quizzes: {}",
        "progress_average": "📈 Average Score: {}%",
        "progress_latest": "🎯 Latest Score: {}%",
        "progress_improving": "📈 Great job! Your scores are improving!",
        "progress_consistent": "📊 You're maintaining consistent performance!",
        "progress_practice": "💪 Keep practicing to improve your scores!",
        "progress_keep_going": "🚀 Keep taking quizzes to track your progress!",
        "progress_error": "❗ Sorry, there was an error generating your progress chart. Please try again later.",
        "progress_command": "View your quiz progress chart",
    },
    "ar": {
        # Start command and welcome
        "hello": "مرحباً",
        "welcome_to_bot": "مرحباً بك في بوت JUSTLearn لقسم علوم الحاسوب.",
        "bot_description": "يمكنني مساعدتك في التدرب على أسئلة الاختيار من متعدد للامتحانات. إليك كيفية استخدامي:",
        "commands_header": "الأوامر",
        "topics_command": "عرض جميع المواضيع المتاحة",
        "adaptive_test_command": "بدء اختبار تكيفي يعدل صعوبته حسب مستواك",
        "mimic_exam_command": "بدء امتحان محاكي للامتحانات الجامعية (الأول، الثاني، النهائي)",
        "results_command": "عرض آخر 5 نتائج اختبارات",
        "reset_command": "إلغاء جلسة الاختبار الحالية",
        "set_reminder_command": "إعداد تذكيرات اختبار يومية",
        "adaptive_test_description": "سيساعدك الاختبار التكيفي في تحديد نقاط القوة والضعف لديك!",
        "language_selection": "يرجى اختيار لغتك المفضلة:",
        "use_start_command": "🏠 استخدم /start للوصول إلى القائمة الرئيسية واستكشاف جميع ميزات البوت!",
        "subjects_command": "عرض جميع المواد المتاحة", 
        "subjects_header": "📚 المواد المتاحة:",
        "subjects_description": "اختر مادة لاستكشاف مواضيعها والاختبارات:",

        # Contact Us Command
        "contact_us_command": "تواصل معنا للدعم والاقتراحات",
        "contact_us_header": "📞 تواصل معنا",
        "contact_us_message": "إذا كنت تريد:\n\n• اقتراح تحسينات\n• الإبلاغ عن أخطاء\n• تقديم أسئلة لتعزيز بنك الأسئلة\n\nيرجى التواصل معنا هنا:\n📧 **just.learn.supp@gmail.com**\n\nنقدر ملاحظاتك ومساهماتك!",

        # Topics list
        "select_subject": "📚 اختر المادة التي تريدها",

        # Adaptive test session
        "active_session": "❗ لديك بالفعل جلسة اختبار نشطة. أكملها أولاً أو استخدم /reset لإلغائها.",
        "welcome_adaptive": "🧠 مرحباً بك في اختبار التقييم التكيفي!\n\nسيساعدك هذا الاختبار في تحديد نقاط القوة والضعف لديك من خلال تعديل صعوبة الأسئلة ديناميكياً.\n\nحدد المواضيع التي تريد تضمينها (يمكنك تحديد عدة مواضيع):",
        "session_expired": "⚠️ انتهت جلستك. يرجى البدء مرة أخرى باستخدام /adaptive_test",
        "select_topics": "حدد المواضيع لاختبارك:",
        "please_select": "⚠️ يرجى تحديد موضوع واحد على الأقل قبل بدء الاختبار.",
        "error_starting": "⚠️ خطأ في بدء الاختبار. يرجى المحاولة مرة أخرى باستخدام /adaptive_test",
        "no_questions": "⚠️ لا توجد أسئلة متاحة لـ {} بصعوبة متوسطة. يرجى تجربة موضوع آخر.",
        "test_started": "🎓 بدأ الاختبار التكيفي!\n\nنبدأ بـ: {}\n\nسيتكيف الاختبار بناءً على إجاباتك. حظاً موفقاً!",
        
        # Question answers
        "correct": "✅ إجابة صحيحة!",
        "incorrect": "❌ إجابة خاطئة!\n\nالإجابة الصحيحة هي: {}\n\n📚 الشرح:\n{}",
        "topic_weak": "❗ يبدو أنك تواجه صعوبة مع {}. تم تحديده كموضوع ضعيف.",
        "moving_next": "🔄 الانتقال إلى الموضوع التالي: {}",
        "no_topic_questions": "⚠️ لا توجد أسئلة متاحة لـ {}. إنهاء الاختبار.",
        "completed": "تم إكمال الاختبار!",
        "max_reached": "تم الوصول إلى الحد الأقصى من الأسئلة لهذا الموضوع. الانتقال إلى الموضوع التالي.",
        "no_more_questions": "لا توجد المزيد من الأسئلة أو المواضيع المتاحة. تم إكمال الاختبار.",
        
        # Next action messages
        "moving_to_hard": "🔄 الانتقال إلى سؤال صعب في نفس الموضوع.",
        "moving_to_medium": "🔄 الانتقال إلى سؤال متوسط في نفس الموضوع.",
        "moving_to_easy": "🔄 الانتقال إلى سؤال سهل في نفس الموضوع.",
        "hard_question_incorrect": "⚠️ لقد أجبت بشكل خاطئ على السؤال الصعب في {}.\n\n📚 اقتراح: راجع هذا الموضوع لتقوية فهمك.",
        "topic_complete_success": "لقد أكملت بنجاح {}. الانتقال إلى الموضوع التالي.",
        "moving_next_question": "الانتقال إلى السؤال التالي.",
        
        # Reevaluation test
        "reevaluation_cleared": "⚠️ تم مسح جلسة الاختبار السابقة لبدء اختبار إعادة تقييم جديد لـ {}.\n\nهام: أسئلة الجلسة السابقة لم تعد نشطة.",
        "starting_reevaluation": "بدء اختبار إعادة التقييم لـ {}...",
        "new_reevaluation": "📝 اختبار إعادة تقييم جديد: {}\n\nيتكون هذا الاختبار من أسئلة بمستويات صعوبة متنوعة.\nلنرى إذا كان بإمكانك تحسين فهمك!",
        "old_session": "⚠️ هذا السؤال من جلسة سابقة لم تعد نشطة.\n\nيرجى الإجابة فقط على أسئلة الجلسة الحالية.",
        "reevaluation_error": "❗ حدث خطأ أثناء بدء اختبار إعادة التقييم. يرجى المحاولة مرة أخرى أو استخدام /reset لمسح جلستك.",
        "reevaluation_skipped": "تم تخطي إعادة التقييم. يمكنك عرض نتائجك باستخدام /results أو بدء اختبار جديد باستخدام /adaptive_test.",
        "returning_adaptive": "🔄 العودة إلى الاختبار التكيفي. الموضوع التالي: {}",
        "reevaluation_completed": "🎓 تم إكمال اختبار إعادة التقييم!\n\n{}\nالنتيجة: {}\n\n",
        "topic_still_weak": "⚠️ {}: ما زال ضعيفاً، يحتاج إلى مراجعة أكثر.\n",
        "topic_improved": "✅ {}: تحسن! عمل جيد.\n",
        "would_like_reevaluation": "هل ترغب في إجراء اختبار إعادة تقييم على '{}'؟",
        "reevaluate_topic": "📚 إعادة تقييم: {}",
        "reevaluation_test": "اختبار إعادة تقييم",
        "advanced_reevaluation_test": "اختبار إعادة تقييم متقدم",
        "advanced_practice_prompt": "هل ترغب في ممارسة متقدمة على '{}' لتحسين أدائك في المستوى العالي؟\n\n📚 **اختبار إعادة التقييم**: 3 أسئلة (1 سهل، 1 متوسط، 1 صعب)\n🔥 **اختبار إعادة التقييم المتقدم**: 3 أسئلة صعبة للإتقان",
        
        # Test completion
        "test_completed": "تم إكمال الاختبار التكيفي!",
        "test_date": "التاريخ: {}",
        "test_score": "النتيجة: {}",
        "topics_tested": "المواضيع المختبرة: {}",
        "topics_to_review": "مواضيع للمراجعة",
        "mastered_topics": "المواضيع المتقنة: {}",
        "topics_needing_advanced_practice": "مواضيع تحتاج ممارسة متقدمة",
        "view_results": "عرض سجل أدائك الكامل باستخدام /results",
        "start_another": "بدء اختبار تكيفي آخر باستخدام /adaptive_test",
        
        # Recommendations
        "recommended_resources": "المصادر الموصى بها",
        "video_tutorial": "فيديو تعليمي",
        "reading_material": "مواد للقراءة",
        
        # UI buttons
        "select_all": "تحديد الكل",
        "clear_all": "مسح الكل",
        "start_test": "بدء الاختبار",
        "select_language": "Select Language / اختر اللغة",
        "language_changed": "تم تغيير اللغة إلى العربية",
        "start_adaptive_button": "🧠 بدء اختبار تكيفي",
        "start_mimic_exam_button": "🎯 بدء امتحان محاكي",
        "return_to_main_menu": "🏠 العودة للقائمة الرئيسية",
        "what_next": "ماذا تريد أن تفعل الآن؟",
        
        # Reset command
        "reset_confirmation": "✅ تم إعادة تعيين جلستك بالكامل.",
        
        # No explanation fallback
        "no_explanation": "لا يوجد شرح متاح.",
        
        # Skip exam details message
        "skip_exam_details": "لقد اخترت تخطي النتائج التفصيلية.",
        
        # Topics command
        "topics_header": "📚 المواضيع المتاحة:",
        "topics_reset": "\n\n✅ تم إعادة تعيين جلستك النشطة.",
        "topics_empty": "لا توجد مواضيع متاحة. يرجى الاتصال بالمسؤول.",
        "start_adaptive_from_topics": "بدء اختبار تكيفي",
        
        # Results command
        "results_header": "📊 نتائج اختباراتك (آخر 5):",
        "results_empty": "📊 لم تقم بإجراء أي اختبارات حتى الآن.",
        "results_test_entry": "{index}. {test_type} ({date})\n   النتيجة: {score}\n   المواضيع الضعيفة: {weak_topics}\n\n",
        "results_weak_topics": "🔍 أهم المواضيع الضعيفة لديك: {topics}",
        "results_no_weak_topics": "لا يوجد",
        
        # Exam completion
        "exam_complete": "✅ اكتمل الاختبار!",
        "your_score": "🧾 نتيجتك: {}",
        "topics_to_review_header": "📉 مواضيع للمراجعة:",
        "no_detailed_questions": "لا توجد أسئلة تفصيلية متاحة لهذا الاختبار.",
        "review_questions_prompt": "هل ترغب في مراجعة الأسئلة والإجابات؟",
        "continue_options": "عرض سجل أدائك الكامل باستخدام /results\nبدء اختبار آخر باستخدام /mimic_incamp_exam",
        "exam_complete_simple": "✅ اكتمل الاختبار! نتيجتك: {}\n\nعرض سجل أدائك الكامل باستخدام /results",
        "show_detailed_button": "عرض النتائج التفصيلية",
        "show_incorrect_button": "عرض الإجابات الخاطئة فقط",
        "skip_details_button": "تخطي التفاصيل",
        "answer_recorded": "تم تسجيل الإجابة {}",
        
        # Mimic exam command
        "mimic_exam_header": "🎯 محاكاة امتحانات الجامعة",
        "mimic_exam_intro": "اختر نوع الامتحان الذي ترغب في إجرائه:",
        # Keep technical terms in English even in Arabic UI
        "first_exam_desc": "1️⃣ الامتحان الأول: Big-O, Arrays, Linked Lists (20 سؤال)",
        "second_exam_desc": "2️⃣ الامتحان الثاني: Stacks, Queues, Recursion, Hashing (20 سؤال)",
        "final_exam_desc": "3️⃣ الامتحان النهائي: All Topics (40 سؤال)",
        "exam_experience_note": "كل امتحان يحاكي بنية وتجربة امتحانات CS211 في الجامعة.",
        
        # First exam
        "first_exam_start": "📝 بدء الامتحان الأول: Big-O, Arrays, Linked Lists\n\nيحتوي هذا الامتحان على 20 سؤال. حظاً موفقاً!",
        
        # Second exam
        "second_exam_header": "🧠 الامتحان الثاني: Stacks, Queues, Recursion, Hashing",
        "second_exam_topics": "يغطي هذا الامتحان Stacks, Queues, Recursion, واختيارياً Hashing.",
        "second_exam_count": "يحتوي الامتحان على 20 سؤال في المجموع.",
        "second_exam_option": "هل ترغب في تضمين أو استبعاد موضوع Hashing؟",
        "include_hashing": "تضمين Hashing",
        "exclude_hashing": "استبعاد Hashing",
        "second_exam_start": "📝 بدء الامتحان الثاني{}.\n\nيحتوي هذا الامتحان على 20 سؤال. حظاً موفقاً!",
        "with_hashing": " مع Hashing",
        
        # Final exam
        "final_exam_header": "📝 الامتحان النهائي: All Topics",
        "final_exam_topics": "يغطي هذا الامتحان جميع مواضيع المقرر.",
        "final_exam_count": "يحتوي الامتحان على 40 سؤال في المجموع.",
        "final_exam_option": "هل ترغب في تضمين أو استبعاد موضوع Big-O؟",
        "include_big_o": "تضمين Big-O",
        "exclude_big_o": "استبعاد Big-O",
        "final_exam_start": "📝 بدء الامتحان النهائي{}.\n\nيحتوي هذا الامتحان على 40 سؤال. حظاً موفقاً!",
        "without_big_o": " بدون Big-O",
        
        # Common exam elements
        "back_to_exam": "العودة إلى اختيار الامتحان",
        "congratulations": "🎉 تهانينا! لم يكن لديك إجابات خاطئة.",
        
        # Reminder command texts
        "reminder_header": "📅 إعدادات التذكير اليومي للاختبارات",
        "reminder_enabled": "✅ التذكيرات اليومية مُفعّلة",
        "reminder_disabled": "❌ التذكيرات اليومية مُعطّلة",
        "reminder_time": "\n🕐 وقت التذكير: {}",
        "reminder_description": "حافظ على انتظام تعلمك! احصل على تذكيرات يومية لممارسة الاختبارات وتحسين أدائك.",
        "no_reminder_active": "لا يوجد تذكير نشط",
        "please_select_reminder_time": "⏰ يرجى اختيار وقت التذكير:",
        "next_reminder": "التذكير التالي: {}",
        "today_at": "اليوم في {}",
        "jordan_time": "(توقيت الأردن)",
        "enable_reminders_first": "❌ يرجى تفعيل التذكيرات أولاً قبل تحديد الوقت.",

        # Reminder buttons  
        "enable_reminder": "🔔 تفعيل التذكيرات اليومية",
        "disable_reminder": "🔕 إلغاء التذكيرات", 
        "change_time_morning": "🌅 الصباح (9:00)",
        "change_time_afternoon": "☀️ بعد الظهر (14:00)",
        "change_time_evening": "🌙 المساء (19:00)", 
        "change_time_custom": "⏰ وقت مخصص",

        # Reminder status messages
        "reminder_turned_on": "✅ تم تفعيل التذكيرات اليومية!",
        "reminder_turned_off": "❌ تم إلغاء التذكيرات اليومية.",
        "reminder_time_updated": "🕐 تم تحديث وقت التذكير إلى {}",
        "reminder_settings_saved": "تم حفظ إعدادات التذكير.",
        "custom_time_instruction": "لتعيين وقت مخصص، يرجى استخدام التوقيت الـ24 ساعة: ‎/set_reminder HH:MM\n\nأمثلة:\n‎/set_reminder 08:30 (8:30 صباحاً)\n‎/set_reminder 20:30 (8:30 مساءً)",
        "notifications_deleted": "🗑️ تم حذف جميع الإشعارات المعلقة.",

        # Daily reminder message
        "daily_reminder_header": "📚 تذكير التعلم اليومي!",
        "daily_reminder_footer": "استمر في العمل الرائع مع دراستك! 💪",
        "reminder_weak_topics": "💡 ركز على المواضيع الضعيفة: {}",
        "reminder_general_suggestion": "💡 التمرين يصنع الإتقان! جرّب اختباراً تكيفياً أو امتحاناً محاكياً.",

        # Progress Command messages
        "progress_no_data": "📊 لم تكمل أي اختبارات حتى الآن. قم بإجراء اختبار أولاً لرؤية تقدمك!",
        "progress_need_more": "📊 تحتاج إلى إكمال المزيد من الاختبارات لعرض تقدمك. استمر في الممارسة!",
        "progress_title": "📈 تقدمك في الاختبارات",
        "progress_total": "📊 إجمالي الاختبارات: {}",
        "progress_average": "📈 متوسط النتيجة: {}%",
        "progress_latest": "🎯 آخر نتيجة: {}%",
        "progress_improving": "📈 عمل رائع! نتائجك تتحسن!",
        "progress_consistent": "📊 أنت تحافظ على أداء ثابت!",
        "progress_practice": "💪 استمر في الممارسة لتحسين نتائجك!",
        "progress_keep_going": "🚀 استمر في إجراء الاختبارات لتتبع تقدمك!",
        "progress_error": "❗ عذراً، حدث خطأ في إنشاء مخطط التقدم. يرجى المحاولة مرة أخرى لاحقاً.",
        "progress_command": "عرض مخطط تقدم الاختبارات",
    }
}
# Keep track of user language preferences
user_languages = {}

# Default language
DEFAULT_LANGUAGE = "en"

def get_user_language(user_id: str) -> str:
    """Get the user's preferred language from database."""
    return db_manager.get_user_language(user_id)

def set_user_language(user_id: str, language: str) -> None:
    """Set the user's preferred language in database."""
    db_manager.set_user_language(user_id, language)

# Define global variables for data storage
user_data = {}
user_selections = {}

# Define constants for topics and difficulty mapping
TOPICS = [
    "Algorithm Analysis and Big-O Notation",
    "Array-Based Lists",
    "Linked Lists",
    "Stacks",
    "Queues",
    "Recursion",
    "Searching and Hashing",
    "Binary Trees",
    "Graphs",
    "Sorting Algorithms"
]

# Mapping to handle different topic naming conventions
TOPIC_MAPPING = {
    "Algorithm Analysis and Big-O Notation": ["Big-O", "Algorithm Analysis", "Algorithmic Analysis", "Big O", "Big-O Notation"],
    "Array-Based Lists": ["Arrays", "Array", "Array-Based", "Array Based Lists"],
    "Linked Lists": ["Linked List", "LinkedList", "LinkedLists"],
    "Stacks": ["Stack"],
    "Queues": ["Queue"],
    "Recursion": ["Recursive"],
    "Searching and Hashing": ["Hashing", "Hash", "Search", "Searching"],
    "Binary Trees": ["Tree", "Trees", "Binary Tree"],
    "Graphs": ["Graph"],
    "Sorting Algorithms": ["Sorting", "Sort Algorithms", "Sort"]
}

# Standardize difficulty levels
DIFFICULTY_MAPPING = {
    "easy": "Easy",
    "medium": "Medium", 
    "med": "Medium",
    "hard": "Hard"
}

# Helper functions for user data management
user_data = {}

def save_user_data(user_data_path=None):
    """Save user data to database (maintains compatibility)."""
    try:
        for user_id, data in user_data.items():
            # Save current session if it exists
            if "current_test_session" in data:
                db_manager.save_user_session(user_id, data["current_test_session"])
            
            # Save weak topics
            if "weak_topic_pool" in data:
                for topic in data["weak_topic_pool"]:
                    db_manager.add_weak_topic(user_id, topic)
            
            # Save needs training topics  
            if "needs_more_training_pool" in data:
                for topic in data["needs_more_training_pool"]:
                    db_manager.add_needs_training_topic(user_id, topic)
                    
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

def load_user_data(user_data_path=None):
    """Load user data from database into memory cache."""
    global user_data
    try:
        # Get all users from database and populate cache
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT user_id FROM users')
            user_ids = [row['user_id'] for row in cursor.fetchall()]
            
            for user_id in user_ids:
                user_data[user_id] = {
                    "tests": db_manager.get_user_tests(user_id, limit=5),
                    "adaptive_tests": [t for t in db_manager.get_user_tests(user_id, limit=5) if t.get("test_type") == "Adaptive Test"][:5],
                    "weak_topic_pool": db_manager.get_weak_topics(user_id),
                    "needs_more_training_pool": db_manager.get_needs_training_topics(user_id),
                    "current_test_session": db_manager.load_user_session(user_id)
                }
                
    except Exception as e:
        logger.error(f"Error loading user data: {e}")
        user_data = {}

def load_recommendations(recommendations_path=None):
    """Load recommendations from database."""
    try:
        return db_manager.load_recommendations()
    except Exception as e:
        logger.error(f"Error loading recommendations: {e}")
        return {}
    
def format_topic_recommendations(topic: str, recommendations: dict, texts: dict, user_id: str) -> str:
    """Format recommendations for a specific topic with topic variation handling."""
    
    # First try exact match
    if topic in recommendations:
        topic_rec = recommendations[topic]
    else:
        # Try to find using topic mapping variations
        topic_rec = None
        found_topic = None
        
        # Check if this topic matches any main topic or variation
        for main_topic, variations in TOPIC_MAPPING.items():
            # Check if our topic is the main topic or in variations
            if topic == main_topic or topic in variations:
                # Try to find recommendation under main topic first
                if main_topic in recommendations:
                    topic_rec = recommendations[main_topic]
                    found_topic = main_topic
                    break
                # Try variations
                else:
                    for variation in variations:
                        if variation in recommendations:
                            topic_rec = recommendations[variation]
                            found_topic = variation
                            break
                    if topic_rec:
                        break
        
        # If still not found, try case-insensitive partial matching
        if not topic_rec:
            for rec_topic, rec_data in recommendations.items():
                if topic.lower() in rec_topic.lower() or rec_topic.lower() in topic.lower():
                    topic_rec = rec_data
                    found_topic = rec_topic
                    break
        
        # If still no match found, return empty
        if not topic_rec:
            return ""
    
    # Get user's language to format correctly
    lang = get_user_language(user_id)
    
    if lang == "ar":
        rec_text = f"\n📚 {texts.get('recommended_resources', 'المصادر الموصى بها')} لموضوع {topic}:\n"
    else:
        rec_text = f"\n📚 {texts.get('recommended_resources', 'Recommended Resources')} for {topic}:\n"
    
    if "youtube" in topic_rec and topic_rec["youtube"]:
        rec_text += f"🎥 {texts.get('video_tutorial', 'Video Tutorial')}: {topic_rec['youtube']}\n"
    
    if "resource" in topic_rec and topic_rec["resource"]:
        rec_text += f"📖 {texts.get('reading_material', 'Reading Material')}: {topic_rec['resource']}\n"
    
    return rec_text

def save_progress_entry(user_id: str, raw_score: str, data_dir: str = "data") -> None:
    """
    Save a normalized progress entry for the user in database.
    
    Args:
        user_id: Telegram user ID
        raw_score: Raw score in format "correct/total" (e.g., "7/10")
        data_dir: Unused parameter (kept for compatibility)
    """
    try:
        # Parse the raw score
        if "/" not in raw_score:
            logger.warning(f"Invalid score format for user {user_id}: {raw_score}")
            return
        
        correct, total = raw_score.split("/")
        correct = int(correct)
        total = int(total)
        
        if total == 0:
            logger.warning(f"Total questions is 0 for user {user_id}")
            return
        
        # Calculate normalized score (0-100)
        normalized_score = (correct / total) * 100
        normalized_score = round(normalized_score, 1)  # Round to 1 decimal place
        
        # Save to database
        db_manager.save_user_progress(user_id, normalized_score)
        
        logger.info(f"Saved progress entry for user {user_id}: {normalized_score}%")
        
    except Exception as e:
        logger.error(f"Error saving progress entry for user {user_id}: {str(e)}")

def load_progress_data(user_id: str, data_dir: str = "data") -> List[Dict]:
    """
    Load progress data for a user from database.
    
    Args:
        user_id: Telegram user ID
        data_dir: Unused parameter (kept for compatibility)
        
    Returns:
        List of progress entries, empty list if no data
    """
    try:
        return db_manager.get_user_progress(user_id)
    except Exception as e:
        logger.error(f"Error loading progress data for user {user_id}: {str(e)}")
        return []

def restore_reminder_jobs_from_db(application) -> None:
    """Restore reminder jobs for all users who have reminders enabled (from database)."""
    try:
        # Jordan timezone
        jordan_tz = pytz.timezone('Asia/Amman')
        now_jordan = datetime.now(jordan_tz)
        
        # Get all users with enabled reminders from database
        users_with_reminders = db_manager.get_all_users_with_reminders()
        
        restored_count = 0
        
        for user_id, reminder_data in users_with_reminders:
            reminder_time = reminder_data.get('time', '09:00')
            
            try:
                # Schedule the reminder job
                hour, minute = map(int, reminder_time.split(':'))
                job_name = f"reminder_{user_id}"
                
                # Remove any existing job for this user
                current_jobs = application.job_queue.get_jobs_by_name(job_name)
                for job in current_jobs:
                    job.schedule_removal()
                
                # Schedule new job with Jordan timezone
                application.job_queue.run_daily(
                    send_daily_reminder,
                    time=time(hour=hour, minute=minute, tzinfo=jordan_tz),
                    data=user_id,
                    name=job_name
                )
                
                restored_count += 1
                logger.info(f"Restored reminder for user {user_id} at {reminder_time} Jordan time")
                
            except Exception as e:
                logger.error(f"Error restoring reminder for user {user_id}: {str(e)}")
        
        logger.info(f"Restored {restored_count} reminder jobs on startup from database")
        logger.info(f"Current Jordan time: {now_jordan.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"Error restoring reminder jobs from database: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def generate_progress_chart(progress_data: List[Dict], texts: Dict = None) -> BytesIO:
    """
    Generate a clear, readable line chart showing user's quiz progress over time.
    Always uses English text regardless of user language to avoid rendering issues.
    
    Args:
        progress_data: List of progress entries with 'date' and 'score' keys
        texts: Dictionary of translated text strings (ignored for chart text)
        
    Returns:
        BytesIO buffer containing the chart image
    """
    try:
        # Extract dates and scores
        dates = []
        scores = []
        
        for entry in progress_data:
            try:
                # Parse date
                date_obj = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M")
                dates.append(date_obj)
                scores.append(float(entry["score"]))
            except (ValueError, KeyError):
                continue
        
        if not dates or not scores:
            raise ValueError("No valid data points found")
        
        # Create the figure with better proportions
        plt.figure(figsize=(14, 8))
        ax = plt.gca()
        
        # Plot all points with enhanced styling
        plt.plot(dates, scores, color='#2E8B57', marker='o', linewidth=4, markersize=15, 
                markerfacecolor='#228B22', markeredgecolor='white', markeredgewidth=3)
        
        # Add score labels for all points
        for i, (date, score) in enumerate(zip(dates, scores)):
            plt.annotate(f'{score:.1f}%', (date, score), textcoords="offset points", 
                       xytext=(0,20), ha='center', fontsize=12, 
                       fontweight='bold', color='#2E8B57',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                               edgecolor='#2E8B57', alpha=0.9))
        
        plt.title('Your Quiz Progress', fontsize=20, fontweight='bold', 
                 pad=25, color='#2C3E50')
        plt.xlabel('Date', fontsize=16, fontweight='bold', color='#34495E')
        plt.ylabel('Score (%)', fontsize=16, fontweight='bold', color='#34495E')
        
        # Set y-axis limits with better padding
        plt.ylim(-5, 105)
        
        # Format x-axis dates for better clarity - always show date + time
        num_points = len(dates)
        
        if num_points <= 5:
            # Show all dates for small datasets
            ax.set_xticks(dates)
            # Always show date + time
            labels = [d.strftime("%m/%d\n%H:%M") for d in dates]
        else:
            # For larger datasets, show subset
            step = max(1, num_points // 5)
            selected_dates = dates[::step]
            ax.set_xticks(selected_dates)
            # Always show date + time for selected dates
            labels = [d.strftime("%m/%d\n%H:%M") for d in selected_dates]
        
        ax.set_xticklabels(labels, fontsize=12, rotation=0)
        
        # Enhanced grid
        plt.grid(True, alpha=0.3, linestyle='-', linewidth=1, color='#BDC3C7')
        ax.set_axisbelow(True)
        
        # Professional styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(2)
        ax.spines['left'].set_color('#34495E')
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['bottom'].set_color('#34495E')
        
        if len(scores) >= 2:
            # Calculate trend using all scores (including 0%)
            first_score = scores[0]
            last_score = scores[-1]
            trend = last_score - first_score
            
            if trend > 5:
                trend_text = '📈 Great improvement!'
                trend_color = '#27AE60'
            elif trend < -5:
                trend_text = '💪 Keep practicing!'
                trend_color = '#F39C12'
            else:
                trend_text = '📊 Steady progress!'
                trend_color = '#3498DB'
            
            plt.text(0.02, 0.98, trend_text, transform=ax.transAxes,
                    fontsize=14, fontweight='bold', color=trend_color,
                    verticalalignment='top',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor='white', 
                            edgecolor=trend_color, alpha=0.9))
        
        # Adjust layout with more padding
        plt.tight_layout(pad=3.0)
        
        # Save with high quality
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0.3)
        buffer.seek(0)
        
        # Close the plot
        plt.close()
        
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating progress chart: {str(e)}")
        plt.close('all')
        raise

def record_quiz_progress(user_id: str, test_results: Dict) -> None:
    """
    Record quiz progress after test completion.
    This function should be called after any quiz/exam completion.
    
    Args:
        user_id: Telegram user ID
        test_results: Test results dictionary containing score information
    """
    try:
        # Extract score from test results
        score = test_results.get("score", "")
        
        if not score:
            logger.warning(f"No score found in test results for user {user_id}")
            return
        
        # Ensure score is in the correct format "correct/total"
        if isinstance(score, str) and "/" in score:
            save_progress_entry(user_id, score)
        else:
            logger.warning(f"Invalid score format for progress tracking: {score}")
            
    except Exception as e:
        logger.error(f"Error recording quiz progress for user {user_id}: {str(e)}")

def get_user_data(user_id: str) -> Dict:
    """Get data for a specific user from database."""
    db_manager.ensure_user_exists(user_id)
    
    return {
        "tests": db_manager.get_user_tests(user_id, limit=5),
        "adaptive_tests": [t for t in db_manager.get_user_tests(user_id, limit=5) if t.get("test_type") == "Adaptive Test"][:5],
        "weak_topic_pool": db_manager.get_weak_topics(user_id),
        "needs_more_training_pool": db_manager.get_needs_training_topics(user_id),
        "current_test_session": db_manager.load_user_session(user_id)
    }

def has_active_test(user_id: str) -> bool:
    """Check if user has an active test session with NUCLEAR advanced reevaluation clearing."""
    # If user doesn't exist in data, definitely no active session
    if user_id not in user_data:
        return False
        
    session = user_data.get(user_id, {}).get("current_test_session")
    
    # If no session, return False
    if session is None:
        return False
    
    # If the session is just an empty dictionary, it's not really active
    if isinstance(session, dict) and not session:
        user_data[user_id]["current_test_session"] = None
        save_user_data()
        logger.warning(f"Empty session for user {user_id}, cleared it")
        return False
    
    # FIXED: Check for completed adaptive test sessions
    test_type = session.get("test_type", "")
    if test_type == "Adaptive Test":
        remaining_topics = session.get("remaining_topics", [])
        # If no remaining topics, the adaptive test is complete
        if not remaining_topics:
            logger.warning(f"NUCLEAR: Clearing completed adaptive test session for user {user_id}")
            user_data[user_id]["current_test_session"] = None
            save_user_data()
            return False
    
    # CRITICAL FIX: NUCLEAR clearing of completed advanced reevaluation sessions
    if "Advanced Reevaluation" in test_type:
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        # If advanced reevaluation test completed (index >= questions length), NUKE IT
        if current_index >= len(questions):
            logger.warning(f"NUCLEAR: Clearing completed advanced reevaluation session for user {user_id}")
            
            # COMPLETE NUCLEAR RESET
            user_data[user_id]["current_test_session"] = None
            
            # Clear ALL session-related data
            if "active_session_ids" in user_data[user_id]:
                user_data[user_id]["active_session_ids"] = {}
            if "session_backup" in user_data[user_id]:
                del user_data[user_id]["session_backup"]
            if "ignore_before_time" in user_data[user_id]:
                user_data[user_id]["ignore_before_time"] = {}
            if "stored_adaptive_session" in user_data[user_id]:
                del user_data[user_id]["stored_adaptive_session"]
                
            save_user_data()
            return False
        
        # ADDITIONAL FIX: Check for stale advanced reevaluation sessions
        session_id = session.get("session_id")
        active_session_id = user_data[user_id].get("active_session_ids", {}).get("reevaluation")
        
        if session_id != active_session_id or not session_id:
            logger.warning(f"NUCLEAR: Clearing stale advanced reevaluation session for user {user_id}")
            user_data[user_id]["current_test_session"] = None
            if "active_session_ids" in user_data[user_id]:
                user_data[user_id]["active_session_ids"] = {}
            save_user_data()
            return False
    
    # ADDITIONAL FIX: Clear any reevaluation session that's been hanging around too long
    if "Reevaluation" in test_type:
        try:
            start_time = datetime.strptime(session["start_time"], "%Y-%m-%d %H:%M:%S")
            elapsed = datetime.now() - start_time
            # 60 minutes timeout for reevaluation tests
            if elapsed.total_seconds() > (60 * 60):
                logger.warning(f"NUCLEAR: Clearing timed-out reevaluation session for user {user_id}")
                user_data[user_id]["current_test_session"] = None
                if "active_session_ids" in user_data[user_id]:
                    user_data[user_id]["active_session_ids"] = {}
                save_user_data()
                return False
        except (ValueError, TypeError):
            # Invalid timestamp, clear the session
            user_data[user_id]["current_test_session"] = None
            save_user_data()
            return False
    
    # Original validation logic for other session types
    required_fields = ["test_type", "start_time"]
    if not all(field in session for field in required_fields):
        user_data[user_id]["current_test_session"] = None
        save_user_data()
        logger.warning(f"Invalid session structure for user {user_id}, reset applied")
        return False
    
    # Check session age (timeout after 30 minutes for non-reevaluation tests)
    try:
        start_time = datetime.strptime(session["start_time"], "%Y-%m-%d %H:%M:%S")
        elapsed = datetime.now() - start_time
        timeout_minutes = 60 if "Reevaluation" in session.get("test_type", "") else 30
        if elapsed.total_seconds() > (timeout_minutes * 60):
            user_data[user_id]["current_test_session"] = None
            save_user_data()
            logger.info(f"Session timed out for user {user_id}")
            return False
    except (ValueError, TypeError):
        user_data[user_id]["current_test_session"] = None
        save_user_data()
        logger.warning(f"Invalid session timestamp for user {user_id}")
        return False
    
    # Check for broken exam sessions
    if "questions" in session and "current_question_index" in session:
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        if not questions or current_index >= len(questions):
            user_data[user_id]["current_test_session"] = None
            save_user_data()
            logger.warning(f"Broken exam session for user {user_id}, reset applied")
            return False
    
    # If we made it here, the session appears valid
    return True

def is_adaptive_test(user_id: str) -> bool:
    """Check if the current test is an adaptive test"""
    session = user_data.get(user_id, {}).get("current_test_session")
    return session is not None and session.get("test_type") == "Adaptive Test"

# MCQ handling functions
def load_mcqs(mcqs_path="data/mcqs.json") -> List[Dict]:
    """Load MCQs from the JSON file."""
    try:
        with open(mcqs_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading MCQs: {e}")
        return []

def get_question_hash(question: Dict) -> str:
    """Generate a unique hash for a question to prevent duplicates."""
    # Use question text + correct answer to create unique identifier
    question_text = question.get("question", "")
    correct_answer = question.get("correct_answer", "")
    choices = str(sorted(question.get("choices", {}).items()))
    
    # Create hash from question content
    content = f"{question_text}|{correct_answer}|{choices}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def enhance_exam_question_selection(questions: List[Dict], target_count: int) -> List[Dict]:
    """Enhanced question selection for exams with better duplicate prevention and shuffling."""
    if not questions:
        return []
    
    # Remove duplicates using hash-based deduplication
    unique_questions = []
    seen_hashes = set()
    
    for question in questions:
        question_hash = get_question_hash(question)
        if question_hash not in seen_hashes:
            seen_hashes.add(question_hash)
            unique_questions.append(question)
    
    # If we have fewer unique questions than needed, use all available
    if len(unique_questions) <= target_count:
        # Shuffle thoroughly
        for _ in range(5):
            random.shuffle(unique_questions)
        return unique_questions
    
    # Enhanced shuffling before selection
    for _ in range(10):  # More rounds for larger pools
        random.shuffle(unique_questions)
    
    # Group by difficulty for balanced selection if possible
    by_difficulty = {"Easy": [], "Medium": [], "Hard": []}
    for q in unique_questions:
        difficulty = q.get("difficulty", "Medium")
        if difficulty in by_difficulty:
            by_difficulty[difficulty].append(q)
    
    # Try to maintain difficulty balance
    selected = []
    difficulties = ["Easy", "Medium", "Hard"]
    
    # Calculate target per difficulty
    per_difficulty = target_count // 3
    remainder = target_count % 3
    
    for i, difficulty in enumerate(difficulties):
        available = by_difficulty[difficulty]
        if available:
            # Shuffle this difficulty's questions
            for _ in range(3):
                random.shuffle(available)
            
            # Take appropriate number
            take_count = per_difficulty
            if i < remainder:  # Distribute remainder to first difficulties
                take_count += 1
            
            selected.extend(available[:min(take_count, len(available))])
    
    # If we still need more questions, take randomly from remaining
    if len(selected) < target_count:
        remaining = [q for q in unique_questions if q not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:target_count - len(selected)])
    
    # Final shuffle of selected questions
    for _ in range(5):
        random.shuffle(selected)
    
    return selected[:target_count]

def get_random_question_by_topic_and_difficulty(topic: str, difficulty: str, all_mcqs: List[Dict]) -> Optional[Dict]:
    """Get a random question with the specified topic and difficulty with enhanced shuffling."""
    # Standardize difficulty
    std_difficulty = DIFFICULTY_MAPPING.get(difficulty.lower(), difficulty)
    
    logger.info(f"Looking for topic '{topic}' with difficulty '{std_difficulty}'")
    
    # Try exact match first
    matching_questions = [
        q for q in all_mcqs 
        if q.get("topic", "") == topic and q.get("difficulty", "") == std_difficulty
    ]
    
    logger.info(f"Exact match found {len(matching_questions)} questions")
    
    # If no exact match, try known variations of the topic name
    if not matching_questions:
        for main_topic, variations in TOPIC_MAPPING.items():
            if topic == main_topic or topic in variations:
                for variation in [main_topic] + variations:
                    new_matches = [
                        q for q in all_mcqs 
                        if q.get("topic", "") == variation and q.get("difficulty", "") == std_difficulty
                    ]
                    matching_questions.extend(new_matches)
        
        logger.info(f"After topic variations: found {len(matching_questions)} questions")
    
    # If still no match, try case-insensitive partial matching
    if not matching_questions:
        matching_questions = [
            q for q in all_mcqs 
            if (topic.lower() in q.get("topic", "").lower() and 
                std_difficulty.lower() in q.get("difficulty", "").lower())
        ]
        
        logger.info(f"After flexible matching: found {len(matching_questions)} questions")
    
    # Last resort: try with any difficulty if the topic matches
    if not matching_questions:
        logger.info(f"Trying with any difficulty for topic '{topic}'")
        matching_questions = [
            q for q in all_mcqs 
            if topic.lower() in q.get("topic", "").lower()
        ]
        
        logger.info(f"With any difficulty: found {len(matching_questions)} questions")
        
        # If we found questions, filter to get the closest difficulty
        if matching_questions:
            # Try to find questions with the closest difficulty
            closest_difficulty = std_difficulty
            
            # If we can't find the exact difficulty, find the closest
            if not any(q.get("difficulty") == std_difficulty for q in matching_questions):
                if std_difficulty == "Medium":
                    # If we want Medium, try Easy then Hard
                    if any(q.get("difficulty") == "Easy" for q in matching_questions):
                        closest_difficulty = "Easy"
                    else:
                        closest_difficulty = "Hard"
                elif std_difficulty == "Easy":
                    closest_difficulty = "Medium"  # If no Easy, try Medium
                elif std_difficulty == "Hard":
                    closest_difficulty = "Medium"  # If no Hard, try Medium
            
            # Filter by closest difficulty
            closest_matches = [
                q for q in matching_questions 
                if q.get("difficulty") == closest_difficulty
            ]
            
            if closest_matches:
                matching_questions = closest_matches
                logger.info(f"Using closest difficulty '{closest_difficulty}': found {len(matching_questions)} questions")
    
    if not matching_questions:
        return None
    
    # ENHANCED: Multiple rounds of shuffling for better randomization
    for _ in range(5):  # More shuffling rounds
        random.shuffle(matching_questions)
    
    # Add some randomness to the selection process
    # Instead of always taking the first, use weighted random selection
    if len(matching_questions) > 1:
        # Create weights that slightly favor questions not at the beginning/end
        weights = []
        for i in range(len(matching_questions)):
            if len(matching_questions) <= 3:
                weight = 1.0  # Equal weights for small lists
            elif i == 0 or i == len(matching_questions) - 1:
                weight = 0.8  # Lower weight for first/last
            else:
                weight = 1.2  # Higher weight for middle questions
            weights.append(weight)
        
        # Use weighted random selection
        selected_question = random.choices(matching_questions, weights=weights, k=1)[0]
    else:
        selected_question = matching_questions[0]
    
    logger.info(f"Selected question with topic '{selected_question.get('topic')}' and difficulty '{selected_question.get('difficulty')}'")
    
    return selected_question

async def show_exam_completion(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, test_results: Dict) -> None:
    """Show a detailed exam completion summary with all questions and explanations.
    
    Located in: simple_bot.py (standalone function)
    
    Args:
        update: Telegram update object
        context: Telegram context object
        user_id: User ID
        test_results: Dictionary containing test results
    """
    # Format completion message
    completion_message = (
        f"✅ Exam Complete!\n\n"
        f"🧾 Your Score: {test_results['score']}\n\n"
    )
    
    # Add weak topics if any
    if test_results.get('weak_topics'):
        completion_message += (
            f"📉 Weak Topics:\n"
            f"- {', '.join(test_results['weak_topics'])}\n\n"
        )
    
    # Send initial summary
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=completion_message
    )
    
    # Send detailed question review
    detailed_message = "📚 Correct Answers & Explanations:\n\n"
    
    # Create counter for numbering questions
    question_number = 1
    
    # Send detailed explanations in chunks to avoid message size limits
    for question in test_results.get('questions', []):
        user_answer = test_results.get('answers', [])[question_number-1] if question_number <= len(test_results.get('answers', [])) else "No answer"
        correct_answer = question.get('correct_answer')
        is_correct = user_answer == correct_answer
        
        # Format question review
        question_review = (
            f"{question_number}. {'✅' if is_correct else '❌'} Question: {question.get('question')}\n"
            f"   Your answer: {user_answer}\n"
            f"   ✅ Correct: {correct_answer}\n"
            f"   📚 Explanation: {question.get('explanation', 'No explanation available.')}\n\n"
        )
        
        # If adding this question would make the message too long, send current message and start a new one
        if len(detailed_message) + len(question_review) > 4000:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=detailed_message
            )
            detailed_message = question_review
        else:
            detailed_message += question_review
        
        question_number += 1
    
    # Send any remaining detailed explanations
    if detailed_message:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=detailed_message
        )
        
    # Final message with options to continue
    final_message = (
        "View your full performance history with /results\n"
        "Start another exam with /mimic_incamp_exam"
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=final_message
    )

# Adaptive test functions
def start_adaptive_test_session(user_id: str, topics: List[str]) -> None:
    """Initialize an adaptive test session with enhanced duplicate tracking"""
    # Use database directly instead of user_data
    session_data = {
        "test_type": "Adaptive Test",
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topics": topics.copy(),
        "remaining_topics": topics.copy(),
        "current_topic_index": 0,
        "current_question": None,
        "completed_topics": [],
        "weak_topics": [],
        "passed_topics": [],
        "needs_more_training": [],  
        "answers": [],
        "questions_asked": {},
        "topic_question_count": {},
        "first_question_state": {},
        "hard_failures_count": {},
        "easy_attempts_after_medium": {},
        "came_from_hard_failure": {},
        # ENHANCED: Add global question tracking
        "used_question_hashes": set()  # This will be converted to list for JSON storage
    }
    
    # Convert set to list for JSON serialization
    if isinstance(session_data["used_question_hashes"], set):
        session_data["used_question_hashes"] = list(session_data["used_question_hashes"])
    
    # Save directly to database
    db_manager.save_user_session(user_id, session_data)
    
    # Update user_data cache if it exists
    if user_id in user_data:
        # Convert back to set for in-memory operations
        session_data["used_question_hashes"] = set(session_data["used_question_hashes"])
        user_data[user_id]["current_test_session"] = session_data
    else:
        user_data[user_id] = get_user_data(user_id)

def get_current_adaptive_topic(user_id: str) -> Optional[str]:
    """Get the current topic for the adaptive test"""
    # Get fresh session from database
    session = db_manager.load_user_session(user_id)
    
    if not session or session.get("test_type") != "Adaptive Test":
        return None
    
    remaining_topics = session.get("remaining_topics", [])
    if not remaining_topics:
        return None
    
    return remaining_topics[0]

def set_current_adaptive_question(user_id: str, question: Dict) -> None:
    """Set the current question in the adaptive test session with enhanced tracking"""
    # Get current session from database
    session = db_manager.load_user_session(user_id)
    
    if not session or session.get("test_type") != "Adaptive Test":
        return
    
    session["current_question"] = question
    
    # Ensure used_question_hashes is properly initialized
    if "used_question_hashes" not in session:
        session["used_question_hashes"] = []
    
    # Convert to set for operations if it's a list
    if isinstance(session["used_question_hashes"], list):
        used_hashes = set(session["used_question_hashes"])
    else:
        used_hashes = session["used_question_hashes"]
    
    # Add current question to used set
    question_hash = get_question_hash(question)
    used_hashes.add(question_hash)
    
    # Convert back to list for JSON storage
    session["used_question_hashes"] = list(used_hashes)
    
    # Save to database
    db_manager.save_user_session(user_id, session)
    
    # Update cache - KEEP SEPARATE COPY with set for in-memory operations
    if user_id in user_data:
        cache_session = session.copy()
        cache_session["used_question_hashes"] = used_hashes  # Keep as set in memory
        user_data[user_id]["current_test_session"] = cache_session

def record_adaptive_answer(user_id: str, is_correct: bool, topic: str, difficulty: str) -> None:
    """Record an answer in the adaptive test session"""
    session = user_data.get(user_id, {}).get("current_test_session")
    
    if not session or session.get("test_type") != "Adaptive Test":
        return
    
    # Record the answer
    session["answers"].append({
        "topic": topic,
        "difficulty": difficulty,
        "correct": is_correct,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    save_user_data()

def move_to_next_adaptive_topic(user_id: str) -> Optional[str]:
    """Move to the next topic in the adaptive test"""
    session = user_data.get(user_id, {}).get("current_test_session")
    
    if not session or session.get("test_type") != "Adaptive Test":
        return None
    
    # Remove current topic from remaining
    if session["remaining_topics"]:
        completed_topic = session["remaining_topics"].pop(0)
        session["completed_topics"].append(completed_topic)
    
    # Get next topic if available
    if session["remaining_topics"]:
        next_topic = session["remaining_topics"][0]
        save_user_data()
        return next_topic
    
    save_user_data()
    return None

def update_adaptive_test_results(user_id: str, result_type: str) -> None:
    """
    Update the results of the adaptive test.

    Args:
        user_id: Telegram user ID
        result_type: Type of result (complete, offer_reevaluation)
    """
    user_info = get_user_data(user_id)
    session = user_info.get("current_test_session")

    if not session or session.get("test_type") != "Adaptive Test":
        return

    # Analyze results
    topic_results = {}
    for answer in session["answers"]:
        topic = answer["topic"]
        if topic not in topic_results:
            topic_results[topic] = {"correct": 0, "total": 0}
        
        topic_results[topic]["total"] += 1
        if answer["correct"]:
            topic_results[topic]["correct"] += 1

    # Mark weak topics (less than 50% correct)
    weak_topics = []
    passed_topics = []
    needs_more_training = session.get("needs_more_training", [])  # NEW
    
    for topic, result in topic_results.items():
        if topic in needs_more_training:
            continue  # Skip topics already marked as needs training
        if result["total"] > 0:
            score = result["correct"] / result["total"]
            if score < 0.5:
                weak_topics.append(topic)
            else:
                passed_topics.append(topic)

    # Update session data
    session["weak_topics"] = weak_topics
    session["passed_topics"] = passed_topics
    session["needs_more_training"] = needs_more_training

    # If test is complete, save to test history
    if result_type == "complete":
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        test_result = {
            "date": current_date,
            "time": current_time,
            "test_type": "Adaptive Test",
            "topics_selected": session["topics"],
            "weak_topics": weak_topics,
            "passed_topics": passed_topics,
            "needs_more_training": needs_more_training
        }
        
        # CRITICAL FIX: Save test to database BEFORE clearing session
        db_manager.save_user_test(user_id, test_result)
        
        # Add to adaptive tests history
        if "adaptive_tests" not in user_info:
            user_info["adaptive_tests"] = []
        
        user_info["adaptive_tests"].insert(0, test_result)
        if len(user_info["adaptive_tests"]) > 5:
            user_info["adaptive_tests"] = user_info["adaptive_tests"][:5]
        
        # Add to regular tests history
        if "tests" not in user_info:
            user_info["tests"] = []
        
        test_entry = {
            "date": current_date,
            "time": current_time,
            "test_type": "Adaptive Test",
            "score": f"{sum(1 for answer in session['answers'] if answer['correct'])}/{len(session['answers'])}",
            "weak_topics": weak_topics,
            "needs_more_training": needs_more_training
        }
        
        user_info["tests"].insert(0, test_entry)
        try:
            record_quiz_progress(user_id, test_entry)
        except Exception as e:
            logger.error(f"Error recording adaptive test progress: {e}")
        if len(user_info["tests"]) > 5:
            user_info["tests"] = user_info["tests"][:5]
        
        # Update weak topic pool
        if "weak_topic_pool" not in user_info:
            user_info["weak_topic_pool"] = []
        
        for topic in weak_topics:
            if topic not in user_info["weak_topic_pool"]:
                user_info["weak_topic_pool"].append(topic)
                # ALSO save to database
                db_manager.add_weak_topic(user_id, topic)
        
        # Update needs more training pool
        if "needs_more_training_pool" not in user_info:
            user_info["needs_more_training_pool"] = []
        
        for topic in needs_more_training:
            if topic not in user_info["needs_more_training_pool"]:
                user_info["needs_more_training_pool"].append(topic)
                # ALSO save to database
                db_manager.add_needs_training_topic(user_id, topic)
        
        # FIXED: Clear session from BOTH global cache and database when completing
        if result_type == "complete":
            user_info["current_test_session"] = None
            db_manager.clear_user_session(user_id)
            logger.info(f"Cleared adaptive test session for user {user_id} in update_adaptive_test_results")

    save_user_data()

def start_reevaluation_test(user_id: str, topic: str, all_mcqs: List[Dict]) -> Dict:
    """Start a reevaluation test for a specific topic - SIMPLIFIED"""
    try:
        logger.info(f"Starting reevaluation for topic {topic} for user {user_id}")
        
        # Get exactly 3 questions in order: Easy, Medium, Hard
        questions = []
        
        # Get one question of each difficulty in specific order
        easy_question = get_random_question_by_topic_and_difficulty(topic, "Easy", all_mcqs)
        medium_question = get_random_question_by_topic_and_difficulty(topic, "Medium", all_mcqs)
        hard_question = get_random_question_by_topic_and_difficulty(topic, "Hard", all_mcqs)
        
        # Add questions in specific order: Easy first, then Medium, then Hard
        if easy_question: 
            questions.append(easy_question)
        if medium_question: 
            questions.append(medium_question)
        if hard_question: 
            questions.append(hard_question)
        
        # Final check: we need at least 1 question to proceed
        if not questions:
            return {"error": f"No questions available for reevaluation on {topic}."}
        
        # Log question count for debugging
        logger.info(f"Reevaluation test for topic '{topic}' has {len(questions)} questions in order: Easy->Medium->Hard")
        
        # Generate a unique session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Create a SIMPLE reevaluation test session - SEQUENTIAL PROCESSING
        session_data = {
            "test_type": f"Reevaluation: {topic}",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "questions": questions,
            "current_question_index": 0,
            "correct_answers": 0,
            "incorrect_topics": [],  # Use list instead of set for better JSON serialization
            "topic": topic,
            "topics": [topic],  # For compatibility with result reporting
            "session_id": session_id,  # Add the session ID to identify this session
            "is_sequential": True  # Flag to indicate this is sequential, not adaptive
        }
        
        # Save to database AND update cache 
        db_manager.save_user_session(user_id, session_data)
        
        # CRITICAL: Update user_data cache so send_question works correctly
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id)
        user_data[user_id]["current_test_session"] = session_data
        save_user_data()
        
        logger.info(f"Successfully created SEQUENTIAL reevaluation session for user {user_id} with {len(questions)} questions")
        
        # Return first question and session ID
        return {
            "first_question": questions[0],
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error in start_reevaluation_test: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Error starting reevaluation test: {str(e)}"}

def start_advanced_reevaluation_test(user_id: str, topic: str, all_mcqs: List[Dict]) -> Dict:
    """Start an advanced reevaluation test with SIMPLE session management"""
    try:
        logger.info(f"Starting advanced reevaluation for topic {topic} for user {user_id}")
        
        # CRITICAL FIX: Don't use get_user_data(), work directly with database
        # Clear session from database directly
        db_manager.clear_user_session(user_id)
        
        # Also clear from cache if it exists
        if user_id in user_data:
            user_data[user_id]["current_test_session"] = None
        
        # Get ONLY hard questions for the topic
        hard_questions = []
        std_difficulty = "Hard"
        
        # Try exact match first
        matching_questions = [
            q for q in all_mcqs 
            if q.get("topic", "") == topic and q.get("difficulty", "") == std_difficulty
        ]
        hard_questions.extend(matching_questions)
        
        # If no exact match, try known variations using TOPIC_MAPPING
        if not hard_questions:
            for main_topic, variations in TOPIC_MAPPING.items():
                if topic == main_topic or topic in variations:
                    # Try the main topic
                    new_matches = [
                        q for q in all_mcqs 
                        if q.get("topic", "") == main_topic and q.get("difficulty", "") == std_difficulty
                    ]
                    hard_questions.extend(new_matches)
                    
                    # Try all variations
                    for variation in variations:
                        new_matches = [
                            q for q in all_mcqs 
                            if q.get("topic", "") == variation and q.get("difficulty", "") == std_difficulty
                        ]
                        hard_questions.extend(new_matches)
        
        # Remove duplicates
        unique_questions = []
        question_texts = set()
        for q in hard_questions:
            question_text = q.get("question", "")[:100]
            if question_text not in question_texts:
                question_texts.add(question_text)
                unique_questions.append(q)
        
        questions = unique_questions
        
        if len(questions) < 2:
            return {"error": f"Not enough hard questions available for advanced reevaluation on {topic}. Need at least 2, found {len(questions)}."}
        
        # Take exactly 3 questions for advanced reevaluation
        if len(questions) > 3:
            questions = random.sample(questions, 3)
        
        # Shuffle the questions
        random.shuffle(questions)
        
        # Create session data
        session_data = {
            "test_type": f"Advanced Reevaluation: {topic}",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "questions": questions,
            "current_question_index": 0,
            "correct_answers": 0,
            "incorrect_topics": [],
            "topic": topic,
            "topics": [topic],
            "is_sequential": True
        }
        
        # Save to database AND update cache (CRITICAL FIX)
        db_manager.save_user_session(user_id, session_data)
        
        # CRITICAL FIX: Update cache so send_question can detect correct test type
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id)
        user_data[user_id]["current_test_session"] = session_data
        save_user_data()
        
        # VERIFICATION: Immediately check if session was saved
        verification_session = db_manager.load_user_session(user_id)
        if not verification_session:
            logger.error(f"CRITICAL: Session was not saved to database for user {user_id}")
            return {"error": "Failed to create session. Please try again."}
        
        logger.info(f"Successfully created and verified SEQUENTIAL advanced reevaluation session for user {user_id} with {len(questions)} hard questions")
        
        return {
            "first_question": questions[0]
        }
    except Exception as e:
        logger.error(f"Error in start_advanced_reevaluation_test: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Error starting advanced reevaluation test: {str(e)}"}

def determine_next_adaptive_action(is_correct: bool, current_difficulty: str, current_topic: str, hard_failures: int = 0, came_from_hard_failure: bool = False) -> Dict:
    """Determine the next action based on the current answer"""
    if is_correct:
        if current_difficulty == "Medium":
            # If we just came from a hard failure, go back to hard for second attempt
            if came_from_hard_failure:
                return {
                    "type": "next_question",
                    "difficulty": "Hard",
                    "topic": current_topic,
                    "message_key": "moving_to_hard",
                    "reset_hard_failure_flag": True  # Reset the flag since we're trying hard again
                }
            else:
                # Normal flow - first time reaching hard
                return {
                    "type": "next_question",
                    "difficulty": "Hard",
                    "topic": current_topic,
                    "message_key": "moving_to_hard"
                }
        elif current_difficulty == "Easy":
            return {
                "type": "next_question",
                "difficulty": "Medium",
                "topic": current_topic,
                "message_key": "moving_to_medium"
            }
        elif current_difficulty == "Hard":
            # Successfully completed this topic
            return {
                "type": "topic_complete",
                "topic": current_topic,
                "message_key": "topic_complete_success",
                "message_format": [current_topic]
            }
    else:  # Incorrect answer
        if current_difficulty == "Medium":
            return {
                "type": "next_question",
                "difficulty": "Easy",
                "topic": current_topic,
                "message_key": "moving_to_easy"
            }
        elif current_difficulty == "Easy":
            # Failed easy question - mark topic as weak and move to next topic
            return {
                "type": "topic_complete", 
                "topic": current_topic,
                "message_key": "topic_weak",
                "message_format": [current_topic]
            }
        elif current_difficulty == "Hard":
            # First hard failure - go to medium with flag set
            # (2nd failure case handled earlier in process_adaptive_answer)
            return {
                "type": "warning",
                "topic": current_topic,
                "message_key": "hard_question_incorrect", 
                "message_format": [current_topic],
                "difficulty": "Medium",
                "set_hard_failure_flag": True
            }
    
    # Default fallback
    return {
        "type": "next_question",
        "difficulty": "Medium",
        "topic": current_topic,
        "message_key": "moving_next_question"
    }

def process_adaptive_answer(user_id: str, answer: str, all_mcqs: List[Dict]) -> Dict:
    """Process an answer in the adaptive test with improved question tracking"""
    try:
        # Get user's language
        lang = get_user_language(user_id)
        texts = TEXTS[lang]
        
        # First verify the user exists in user_data
        if user_id not in user_data:
            logger.warning(f"User {user_id} not found in user_data")
            return {"error": "User session not found. Please start a new test with /adaptive_test."}
        
        # Verify session exists
        session = user_data[user_id].get("current_test_session")
        if not session:
            logger.warning(f"No active session for user {user_id}")
            return {"error": "No active test session. Please start a new test."}
        
        # Verify session type
        if session.get("test_type") != "Adaptive Test":
            logger.warning(f"Session type mismatch for user {user_id}: {session.get('test_type')}")
            return {"error": "This is not an adaptive test session."}
        
        # Verify current question exists
        current_question = session.get("current_question")
        if not current_question:
            logger.warning(f"No current question in session for user {user_id}")
            return {"error": "No current question. Please start a new test."}
        
        # Check if the answer is correct
        is_correct = answer.upper() == current_question.get("correct_answer", "").upper()
        current_topic = current_question.get("topic", "")
        current_difficulty = current_question.get("difficulty", "")
        
        # Record the answer
        record_adaptive_answer(user_id, is_correct, current_topic, current_difficulty)
        
        # Initialize tracking structures if they don't exist
        if "questions_asked" not in session:
            session["questions_asked"] = {}
        if "topic_question_count" not in session:
            session["topic_question_count"] = {}
        if "first_question_state" not in session:
            session["first_question_state"] = {}
        if "hard_failures_count" not in session:
            session["hard_failures_count"] = {}
        if "came_from_hard_failure" not in session:
            session["came_from_hard_failure"] = {}
        if "easy_attempts_after_medium" not in session:
            session["easy_attempts_after_medium"] = {}
        
        # Initialize tracking for this topic
        if current_topic not in session["hard_failures_count"]:
            session["hard_failures_count"][current_topic] = 0
        if current_topic not in session["came_from_hard_failure"]:
            session["came_from_hard_failure"][current_topic] = False
        if current_topic not in session["easy_attempts_after_medium"]:
            session["easy_attempts_after_medium"][current_topic] = 0
        
        # Initialize first question state for this topic if not exists
        if current_topic not in session["first_question_state"]:
            session["first_question_state"][current_topic] = {
                "is_first_question": True,
                "first_was_medium": False,
                "gave_second_easy": False
            }
        
        first_state = session["first_question_state"][current_topic]
        
        # CRITICAL FIX: Handle the special first question sequence FIRST
        if first_state["is_first_question"]:
            if current_difficulty == "Medium":
                first_state["first_was_medium"] = True
                if is_correct:
                    # Medium correct - mark first question as done and continue to Hard
                    first_state["is_first_question"] = False
                else:
                    # Medium wrong - will go to Easy, but don't mark first question as done yet
                    # Save session state before proceeding
                    db_manager.save_user_session(user_id, session)
                    user_data[user_id]["current_test_session"] = session
                    
                    # Continue to regular adaptive logic which will give Easy
                    pass
                        
            elif current_difficulty == "Easy" and first_state["first_was_medium"]:
                session["easy_attempts_after_medium"][current_topic] += 1
                easy_attempts = session["easy_attempts_after_medium"][current_topic]
                
                if not is_correct:
                    if easy_attempts < 2:  # First easy wrong - give another easy
                        logger.info(f"First easy wrong for {current_topic}, giving second easy attempt")
                        
                        # Save session state before getting next question
                        db_manager.save_user_session(user_id, session)
                        user_data[user_id]["current_test_session"] = session
                        
                        # Get another Easy question
                        next_question = get_unused_question_by_topic_and_difficulty(user_id, current_topic, "Easy", all_mcqs)
                        if next_question:
                            set_current_adaptive_question(user_id, next_question)
                            return {
                                "correct": is_correct,
                                "question": current_question,
                                "correct_answer": current_question.get("correct_answer", ""),
                                "explanation": current_question.get("explanation", ""),
                                "next_action": {
                                    "type": "next_question",
                                    "difficulty": "Easy",
                                    "topic": current_topic,
                                    "message": texts["moving_to_easy"]
                                },
                                "next_question": next_question
                            }
                        else:
                            # No more easy questions available - mark as weak
                            first_state["is_first_question"] = False
                            db_manager.save_user_session(user_id, session)
                            user_data[user_id]["current_test_session"] = session
                            return {
                                "correct": is_correct,
                                "question": current_question,
                                "correct_answer": current_question.get("correct_answer", ""),
                                "explanation": current_question.get("explanation", ""),
                                "next_action": {
                                    "type": "mark_weak_and_continue",
                                    "topic": current_topic,
                                    "message": texts["topic_weak"].format(current_topic)
                                }
                            }
                    else:  # Second easy wrong - mark as weak and move on
                        logger.info(f"Second easy wrong for {current_topic}, marking as weak")
                        first_state["is_first_question"] = False
                        db_manager.save_user_session(user_id, session)
                        user_data[user_id]["current_test_session"] = session
                        return {
                            "correct": is_correct,
                            "question": current_question,
                            "correct_answer": current_question.get("correct_answer", ""),
                            "explanation": current_question.get("explanation", ""),
                            "next_action": {
                                "type": "mark_weak_and_continue",
                                "topic": current_topic,
                                "message": texts["topic_weak"].format(current_topic)
                            }
                        }
                else:  # Easy correct after medium wrong - continue normally
                    first_state["is_first_question"] = False
                    # Continue to regular adaptive logic below
        
        # CRITICAL FIX: Update hard failures count and check immediately
        if current_difficulty == "Hard" and not is_correct:
            session["hard_failures_count"][current_topic] += 1
            logger.info(f"Hard failure count for {current_topic}: {session['hard_failures_count'][current_topic]}")
            
            # SAVE SESSION IMMEDIATELY to persist the count
            db_manager.save_user_session(user_id, session)
            user_data[user_id]["current_test_session"] = session
            
            # Check if this is the 2nd hard failure - terminate immediately
            if session["hard_failures_count"][current_topic] >= 2:
                logger.info(f"TERMINATING: Two hard failures for {current_topic}")
                if "needs_more_training" not in session:
                    session["needs_more_training"] = []
                if current_topic not in session["needs_more_training"]:
                    session["needs_more_training"].append(current_topic)
                
                db_manager.save_user_session(user_id, session)
                user_data[user_id]["current_test_session"] = session
                
                return {
                    "correct": is_correct,
                    "question": current_question,
                    "correct_answer": current_question.get("correct_answer", ""),
                    "explanation": current_question.get("explanation", ""),
                    "next_action": {
                        "type": "needs_training_complete",
                        "topic": current_topic,
                        "message": texts.get("needs_more_training", 
                            f"You're doing well with {current_topic} but need more practice on high-level questions. Moving to next topic.")
                    }
                }
        
        # Add current question to asked questions tracking
        if current_topic not in session["questions_asked"]:
            session["questions_asked"][current_topic] = {"Easy": [], "Medium": [], "Hard": []}
        if current_difficulty not in session["questions_asked"][current_topic]:
            session["questions_asked"][current_topic][current_difficulty] = []
        
        question_id = current_question.get("question", "")[:50]
        if question_id not in session["questions_asked"][current_topic][current_difficulty]:
            session["questions_asked"][current_topic][current_difficulty].append(question_id)
        
        # Update topic question count
        if current_topic not in session["topic_question_count"]:
            session["topic_question_count"][current_topic] = 1
        else:
            session["topic_question_count"][current_topic] += 1
        
        # Continue with normal logic for other cases
        # Get tracking variables  
        hard_failures = session["hard_failures_count"].get(current_topic, 0)
        came_from_hard_failure = session["came_from_hard_failure"].get(current_topic, False)
        
        # Use regular adaptive logic
        next_action = determine_next_adaptive_action(is_correct, current_difficulty, current_topic, hard_failures, came_from_hard_failure)
        
        # Check if we need to override question limit BEFORE updating flags
        is_critical_hard_retry = (
            next_action.get("type") == "next_question" and 
            next_action.get("difficulty") == "Hard" and 
            session["came_from_hard_failure"].get(current_topic, False)
        )
        
        # Handle flag updates from next_action (AFTER checking for critical retry)
        if "set_hard_failure_flag" in next_action:
            session["came_from_hard_failure"][current_topic] = True
            del next_action["set_hard_failure_flag"]
        
        if "reset_hard_failure_flag" in next_action:
            session["came_from_hard_failure"][current_topic] = False
            del next_action["reset_hard_failure_flag"]
        
        # Process message key to get translated message
        if "message_key" in next_action and next_action["message_key"] in texts:
            message_key = next_action["message_key"]
            if "message_format" in next_action:
                next_action["message"] = texts[message_key].format(*next_action["message_format"])
            else:
                next_action["message"] = texts[message_key]
            
            del next_action["message_key"]
            if "message_format" in next_action:
                del next_action["message_format"]
        
        result = {
            "correct": is_correct,
            "question": current_question,
            "correct_answer": current_question.get("correct_answer", ""),
            "explanation": current_question.get("explanation", ""),
            "next_action": next_action
        }
        
        # REMOVED the problematic early termination for Easy wrong
        # This was causing the second easy chance to be skipped
        
        # FIXED: Handle completion cases - Check if more topics before showing completion
        if next_action["type"] in ["complete", "offer_reevaluation", "topic_complete"]:
            if next_action["type"] == "topic_complete":
                # Check if there are more topics BEFORE showing completion message
                next_topic = move_to_next_adaptive_topic(user_id)
                
                if next_topic:
                    # There are more topics - get next question and continue
                    next_question = get_unused_question_by_topic_and_difficulty(user_id, next_topic, "Medium", all_mcqs)
                    if next_question:
                        set_current_adaptive_question(user_id, next_question)
                        result["next_question"] = next_question
                        result["next_action"] = {
                            "type": "next_topic",
                            "topic": next_topic,
                            "message": texts["moving_next"].format(next_topic)
                        }
                        return result
                
                # No more topics - complete the test
                update_adaptive_test_results(user_id, "complete")
                result["show_completion"] = True
                return result
            else:
                # Handle other completion types
                update_adaptive_test_results(user_id, next_action["type"])
                result["show_completion"] = (next_action["type"] == "complete")
                return result
        
        # Check if we've reached the maximum questions for this topic (5)
        # BUT allow one more if it's a critical hard retry
        max_questions_per_topic = 5
        current_question_count = session["topic_question_count"].get(current_topic, 0)
        
        if current_question_count >= max_questions_per_topic and not is_critical_hard_retry:
            logger.info(f"Topic {current_topic} has reached max questions ({max_questions_per_topic}). Moving to next topic.")
            return {
                "correct": is_correct,
                "question": current_question,
                "correct_answer": current_question.get("correct_answer", ""),
                "explanation": current_question.get("explanation", ""),
                "next_action": {
                    "type": "topic_max_reached",
                    "topic": current_topic,
                    "message": texts["max_reached"]
                }
            }
        
        # Get next question based on next_action
        next_topic = next_action.get("topic", current_topic)
        next_difficulty = next_action.get("difficulty")
        
        # For critical hard retry, try unused first, then allow reuse only if no alternatives
        if is_critical_hard_retry:
            # First try to get an unused hard question
            next_question = get_unused_question_by_topic_and_difficulty(user_id, next_topic, next_difficulty, all_mcqs)
            
            # If no unused hard questions available, only then allow reuse for critical retry
            if not next_question:
                next_question = get_random_question_by_topic_and_difficulty(next_topic, next_difficulty, all_mcqs)
        else:
            next_question = get_unused_question_by_topic_and_difficulty(user_id, next_topic, next_difficulty, all_mcqs)
        
        if not next_question:
            session = user_data.get(user_id, {}).get("current_test_session")
            if session and len(session.get("remaining_topics", [])) > 0:
                next_topic = move_to_next_adaptive_topic(user_id)
                
                if next_topic:
                    next_question = get_unused_question_by_topic_and_difficulty(user_id, next_topic, "Medium", all_mcqs)
        
        if next_question:
            set_current_adaptive_question(user_id, next_question)
            result["next_question"] = next_question
        else:
            update_adaptive_test_results(user_id, "complete")
            result["next_action"] = {
                "type": "complete", 
                "message": texts["no_more_questions"]
            }
            # Add flag to show completion in button_handler
            result["show_completion"] = True
        
        return result
    except Exception as e:
        logger.error(f"Error in process_adaptive_answer for user {user_id}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "error": "An error occurred while processing your answer. Please try again or use /reset if you continue to have issues."
        }
    
def get_unused_question_by_topic_and_difficulty(user_id: str, topic: str, difficulty: str, all_mcqs: List[Dict]) -> Optional[Dict]:
    """Get a question that hasn't been used yet with enhanced duplicate prevention."""
    
    # SAFETY CHECK: Handle None difficulty
    if difficulty is None:
        difficulty = "Medium"
        logger.warning(f"Difficulty was None for topic {topic}, defaulting to Medium")
    
    session = user_data.get(user_id, {}).get("current_test_session")
    if not session:
        return get_random_question_by_topic_and_difficulty(topic, difficulty, all_mcqs)
    
    # Initialize or convert used_question_hashes
    if "used_question_hashes" not in session:
        session["used_question_hashes"] = set()
    elif isinstance(session["used_question_hashes"], list):
        session["used_question_hashes"] = set(session["used_question_hashes"])
    
    # Get tracking data
    questions_asked = session.get("questions_asked", {})
    if topic not in questions_asked:
        questions_asked[topic] = {"Easy": [], "Medium": [], "Hard": []}
    if difficulty not in questions_asked[topic]:
        questions_asked[topic][difficulty] = []
    
    asked_for_topic_difficulty = questions_asked[topic][difficulty]
    
    # Get all questions matching topic and difficulty
    matching_questions = []
    std_difficulty = DIFFICULTY_MAPPING.get(difficulty.lower(), difficulty)
    
    # Try exact match first
    matching_questions = [
        q for q in all_mcqs 
        if q.get("topic", "") == topic and q.get("difficulty", "") == std_difficulty
    ]
    
    # If no exact match, try known variations
    if not matching_questions:
        for main_topic, variations in TOPIC_MAPPING.items():
            if topic == main_topic or topic in variations:
                for variation in [main_topic] + variations:
                    new_matches = [
                        q for q in all_mcqs 
                        if q.get("topic", "") == variation and q.get("difficulty", "") == std_difficulty
                    ]
                    matching_questions.extend(new_matches)
    
    # Enhanced filtering using hash-based tracking
    unused_questions = []
    for q in matching_questions:
        question_hash = get_question_hash(q)
        question_id = q.get("question", "")[:50]  # Keep old method for compatibility
        
        # Check both global hash tracking and local ID tracking
        if (question_hash not in session["used_question_hashes"] and 
            question_id not in asked_for_topic_difficulty):
            unused_questions.append(q)
    
    # Enhanced shuffling and selection
    if unused_questions:
        # Multiple rounds of shuffling for better randomization
        for _ in range(5):
            random.shuffle(unused_questions)
        
        # Use weighted random selection if enough questions
        if len(unused_questions) > 1:
            selected_question = random.choice(unused_questions)
        else:
            selected_question = unused_questions[0]
        
        # Track the selected question globally and locally
        question_hash = get_question_hash(selected_question)
        question_id = selected_question.get("question", "")[:50]
        
        session["used_question_hashes"].add(question_hash)
        asked_for_topic_difficulty.append(question_id)
        
        # Update session in database (convert set to list for JSON)
        session_for_db = session.copy()
        session_for_db["used_question_hashes"] = list(session["used_question_hashes"])
        db_manager.save_user_session(user_id, session_for_db)
        
        return selected_question
    
    # If all questions have been used, try other difficulties
    if matching_questions:
        logger.info(f"All {difficulty} questions for {topic} have been used. Trying other difficulties.")
        
        # Try to find unused questions in other difficulties for this topic
        all_topic_questions = []
        for alt_difficulty in ["Easy", "Medium", "Hard"]:
            if alt_difficulty != difficulty:
                alt_matches = [
                    q for q in all_mcqs 
                    if q.get("topic", "") == topic and q.get("difficulty", "") == alt_difficulty
                ]
                all_topic_questions.extend(alt_matches)
        
        # Filter by global hash to avoid any duplicates
        truly_unused = []
        for q in all_topic_questions:
            question_hash = get_question_hash(q)
            if question_hash not in session["used_question_hashes"]:
                truly_unused.append(q)
        
        if truly_unused:
            # Enhanced shuffling and selection
            for _ in range(5):
                random.shuffle(truly_unused)
            
            selected_question = random.choice(truly_unused)
            question_hash = get_question_hash(selected_question)
            session["used_question_hashes"].add(question_hash)
            
            # Update session in database
            session_for_db = session.copy()
            session_for_db["used_question_hashes"] = list(session["used_question_hashes"])
            db_manager.save_user_session(user_id, session_for_db)
            
            logger.info(f"Selected {selected_question.get('difficulty')} question instead of {difficulty} for {topic}")
            return selected_question
        
        # Last resort: return a random question but mark it
        logger.warning(f"All questions for topic {topic} have been used. Returning random question.")
        for _ in range(3):
            random.shuffle(matching_questions)
        
        selected_question = random.choice(matching_questions)
        question_hash = get_question_hash(selected_question)
        session["used_question_hashes"].add(question_hash)
        
        # Update session in database
        session_for_db = session.copy()
        session_for_db["used_question_hashes"] = list(session["used_question_hashes"])
        db_manager.save_user_session(user_id, session_for_db)
        
        return selected_question
    
    # If no matches at all, try with any difficulty as a fallback
    return get_random_question_by_topic_and_difficulty(topic, difficulty, all_mcqs)

def process_reevaluation_answer(user_id: str, answer: str) -> Dict:
    """Process an answer in the NORMAL reevaluation test with SIMPLE SEQUENTIAL LOGIC"""
    try:
        # GET SESSION FROM DATABASE, NOT CACHE
        session = db_manager.load_user_session(user_id)
        
        # Verify session exists
        if not session:
            return {"error": "No active test session. Please start a new test."}
        
        # Verify session type - ONLY process normal reevaluation here
        test_type = session.get("test_type", "")
        if not test_type.startswith("Reevaluation") or "Advanced" in test_type:
            return {"error": "This is not a normal reevaluation test session."}
            
        # Ensure this is sequential processing
        is_sequential = session.get("is_sequential", True)
        if not is_sequential:
            return {"error": "This session is not configured for sequential processing."}
            
        # Get question data
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        logger.info(f"Processing SEQUENTIAL reevaluation answer for user {user_id}, question {current_index + 1}/{len(questions)}")
        
        if current_index >= len(questions):
            return {"error": "No more questions in this test."}
        
        # Process the answer - SIMPLE SEQUENTIAL LOGIC
        question = questions[current_index]
        is_correct = answer.upper() == question.get("correct_answer", "").upper()
        
        # Update session data - SIMPLE SEQUENTIAL LOGIC
        if "correct_answers" not in session:
            session["correct_answers"] = 0
            
        if is_correct:
            session["correct_answers"] += 1
        else:
            # Add to incorrect topics (as a list to avoid serialization issues)
            if "incorrect_topics" not in session:
                session["incorrect_topics"] = []
            
            topic = question.get("topic", "")
            if topic and topic not in session["incorrect_topics"]:
                session["incorrect_topics"].append(topic)
        
        # SIMPLE SEQUENTIAL LOGIC: Just move to next question
        session["current_question_index"] = current_index + 1
        
        # Save updated session TO DATABASE AND UPDATE CACHE
        db_manager.save_user_session(user_id, session)
        if user_id in user_data:
            user_data[user_id]["current_test_session"] = session
        save_user_data()
        
        # Check if test is completed
        test_completed = session["current_question_index"] >= len(questions)
        
        result = {
            "correct": is_correct,
            "question": question,
            "correct_answer": question.get("correct_answer", ""),
            "explanation": question.get("explanation", ""),
            "test_completed": test_completed
        }
        
        if test_completed:
            # Complete the reevaluation test
            topics = session.get("topics", [session.get("topic", "Unknown")])
            correct_answers = session.get("correct_answers", 0)
            total_questions = len(questions)
            
            # Determine weak topics - for reevaluation, if less than 2/3 correct
            weak_topics = []
            if correct_answers < (total_questions * 2 // 3):  # Less than 2/3 correct
                weak_topics = topics.copy()
            
            # Create test result
            test_result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "test_type": f"Reevaluation: {topics[0] if topics else 'Unknown'}",
                "topics": topics,
                "score": f"{correct_answers}/{total_questions}",
                "weak_topics": weak_topics
            }
            
            # Save to database
            db_manager.save_user_test(user_id, test_result)
            
            # Update weak topic pool
            for topic in weak_topics:
                db_manager.add_weak_topic(user_id, topic)
            
            # Record progress for visual tracking
            try:
                if total_questions > 0:
                    normalized_score = (correct_answers / total_questions) * 100
                    db_manager.save_user_progress(user_id, normalized_score)
            except Exception as e:
                logger.error(f"Error recording reevaluation progress: {e}")
            
            # Clear session FROM BOTH DATABASE AND CACHE
            if user_id in user_data:
                user_data[user_id]["current_test_session"] = None
            db_manager.clear_user_session(user_id)
            save_user_data()
            
            result["test_results"] = test_result
        else:
            # Get next question - SIMPLE: just get the next one in sequence
            result["next_question"] = questions[session["current_question_index"]]
        
        return result
    except Exception as e:
        # Log the error
        logger.error(f"Error in process_reevaluation_answer for user {user_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "error": f"An error occurred while processing your answer: {str(e)}. Please try again or use /reset."
        }
    
def process_reevaluation_answer_advanced(user_id: str, answer: str) -> Dict:
    """Enhanced process reevaluation answer - PURELY SEQUENTIAL FOR ADVANCED REEVAL"""
    try:
        logger.info(f"Processing ADVANCED reevaluation answer for user {user_id}: {answer}")
        
        # CRITICAL FIX: Get fresh session from database instead of stale cache
        session = db_manager.load_user_session(user_id)
        
        # Simple session validation
        if not session:
            logger.warning(f"No current_test_session found for user {user_id}")
            return {"error": "No active test session. Please start a new test."}
        
        if not isinstance(session, dict):
            logger.warning(f"Invalid session type for user {user_id}: {type(session)}")
            return {"error": "Invalid session format. Please start a new test."}
        
        test_type = session.get("test_type", "")
        
        if not test_type.startswith("Advanced Reevaluation"):
            logger.warning(f"Invalid test type for advanced reevaluation: {test_type}")
            return {"error": "This is not an advanced reevaluation test session."}
        
        # Get question data - PURELY SEQUENTIAL
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        if current_index >= len(questions):
            logger.warning(f"Question index out of range for user {user_id}: {current_index} >= {len(questions)}")
            return {"error": "No more questions in this test."}
        
        # Process the answer - SIMPLE SEQUENTIAL LOGIC ONLY
        question = questions[current_index]
        is_correct = answer.upper() == question.get("correct_answer", "").upper()
        
        # Update session data - SIMPLE INCREMENTAL
        if "correct_answers" not in session:
            session["correct_answers"] = 0
            
        if is_correct:
            session["correct_answers"] += 1
        else:
            # ENSURE it's a list for JSON serialization
            if "incorrect_topics" not in session:
                session["incorrect_topics"] = []
            
            # CONVERT SET TO LIST if needed
            if isinstance(session["incorrect_topics"], set):
                session["incorrect_topics"] = list(session["incorrect_topics"])
            
            # ENSURE it's a list
            if not isinstance(session["incorrect_topics"], list):
                session["incorrect_topics"] = []
            
            topic = question.get("topic", "")
            if topic and topic not in session["incorrect_topics"]:
                session["incorrect_topics"].append(topic)
        
        # Move to next question - SIMPLE INCREMENT
        session["current_question_index"] = current_index + 1
        
        # Save to database and update cache
        db_manager.save_user_session(user_id, session)
        
        # CRITICAL FIX: Update cache to match database
        if user_id in user_data:
            user_data[user_id]["current_test_session"] = session
        save_user_data()
        
        # Check if test is completed - SIMPLE INDEX CHECK
        test_completed = session["current_question_index"] >= len(questions)
        
        result = {
            "correct": is_correct,
            "question": question,
            "correct_answer": question.get("correct_answer", ""),
            "explanation": question.get("explanation", ""),
            "test_completed": test_completed
        }
        
        if test_completed:
            logger.info(f"Advanced reevaluation test completed for user {user_id}")
            
            # Complete the reevaluation test
            topics = session.get("topics", [session.get("topic", "Unknown")])
            correct_answers = session.get("correct_answers", 0)
            total_questions = len(questions)
            
            # Determine weak topics - for ADVANCED reevaluation, if less than 80% correct
            weak_topics = []
            if correct_answers < (total_questions * 0.8):  # Less than 80% for advanced
                weak_topics = topics.copy()
            
            # Create test result
            test_result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "test_type": test_type,
                "topics": topics,
                "score": f"{correct_answers}/{total_questions}",
                "weak_topics": weak_topics
            }
            
            # Save to database
            db_manager.save_user_test(user_id, test_result)
            
            # Update weak topic pool
            for topic in weak_topics:
                db_manager.add_weak_topic(user_id, topic)
            
            # Record progress
            try:
                if total_questions > 0:
                    normalized_score = (correct_answers / total_questions) * 100
                    db_manager.save_user_progress(user_id, normalized_score)
            except Exception as e:
                logger.error(f"Error recording advanced reevaluation progress: {e}")
            
            # Clear session
            if user_id in user_data:
                user_data[user_id]["current_test_session"] = None
            db_manager.clear_user_session(user_id)
            save_user_data()
            
            result["test_results"] = test_result
        else:
            # Get next question - SIMPLE SEQUENTIAL: just get the next one in sequence
            if session["current_question_index"] < len(questions):
                result["next_question"] = questions[session["current_question_index"]]
            else:
                logger.warning(f"No next question available for user {user_id}")
        
        return result
    except Exception as e:
        logger.error(f"Critical error in process_reevaluation_answer_advanced for user {user_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "error": f"An error occurred while processing your answer: {str(e)}. Please try again or use /reset."
        }
    
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    user_id = str(user.id)
    
    # Get the current language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    welcome_message = (
        f"👋 {texts['hello']} {user.first_name}! {texts['welcome_to_bot']}\n\n"
        f"{texts['bot_description']}\n\n"
        f"{texts['language_selection']}\n"
        f"To change the language, click below / لتغيير اللغة، انقر أدناه\n\n"
        f"📋 {texts['commands_header']}:\n"
        f"/subjects - {texts['subjects_command']}\n"
        f"/topics - {texts['topics_command']}\n"
        f"/adaptive_test - {texts['adaptive_test_command']}\n"
        f"/mimic_incamp_exam - {texts['mimic_exam_command']}\n"
        f"/results - {texts['results_command']}\n"
        f"/progress - {texts.get('progress_command', 'View your quiz progress chart')}\n"
        f"/set_reminder - {texts['set_reminder_command']}\n"
        f"/reset - {texts['reset_command']}\n"
        f"/contact_us - {texts['contact_us_command']}\n\n"
        f"✏️ {texts['adaptive_test_description']}"
    )
    
    # Create language selection button only
    keyboard = [
        [InlineKeyboardButton("Select Language / اختر اللغة", callback_data="show_languages")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def subjects_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /subjects command."""
    user_id = str(update.effective_user.id)
    
    # Get user's language preference
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Always reset the session when viewing subjects
    user_info = get_user_data(user_id)
    if "current_test_session" in user_info and user_info["current_test_session"] is not None:
        user_info["current_test_session"] = None
        save_user_data()
    
    # Clear any selections data
    if user_id in user_selections:
        del user_selections[user_id]
    
    # Create subjects list
    subjects_message = f"{texts['subjects_header']}\n\n{texts['subjects_description']}\n\n"
    subjects_message += "• CS211 - Data Structures\n\n"
    
    keyboard = [
        [InlineKeyboardButton("CS211 - Data Structures", callback_data="select_subject:CS211")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        subjects_message,
        reply_markup=reply_markup
    )

async def topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /topics command."""
    user_id = str(update.effective_user.id)
    
    # Get user's language preference
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Always reset the session when viewing topics
    user_info = get_user_data(user_id)
    if "current_test_session" in user_info and user_info["current_test_session"] is not None:
        user_info["current_test_session"] = None
        save_user_data()
    
    # Clear any selections data
    if user_id in user_selections:
        del user_selections[user_id]
    
    # Show subject selection first
    keyboard = [
        [InlineKeyboardButton("CS211 DATA STRUCTURE", callback_data="subject_topics:CS211")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        texts["select_subject"],
        reply_markup=reply_markup
    )

async def results_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /results command."""
    user_id = str(update.effective_user.id)
    
    # Debug print
    print(f"Results requested for user {user_id}")
    user_info = get_user_data(user_id)
    print(f"User has {len(user_info.get('tests', []))} test results")
    for test in user_info.get('tests', []):
        print(f"  Test: {test.get('test_type')}, Score: {test.get('score')}")
    
    # Get user's language preference
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Get test results
    test_results = user_info.get("tests", [])
    
    if not test_results:
        await update.message.reply_text(texts["results_empty"])
        return
        
    # Format results message
    results_message = texts["results_header"] + "\n\n"
    
    for i, test in enumerate(test_results):
        # Format the weak topics string
        weak_topics_str = ", ".join(test.get('weak_topics', [])) if test.get('weak_topics', []) else texts["results_no_weak_topics"]
        
        # Add time if available, otherwise just show date
        date_str = test.get('date', 'N/A')
        time_str = test.get('time', '')
        if time_str:
            date_str = f"{date_str} {time_str}"
        
        # Format this entry using the template from translations
        entry = texts["results_test_entry"].format(
            index=i+1,
            test_type=test.get('test_type', 'Test'),
            date=date_str,
            score=test.get('score', 'N/A'),
            weak_topics=weak_topics_str
        )
        results_message += entry
    
    # Get overall weak topics
    weak_topics = user_info.get("weak_topic_pool", [])
    if weak_topics:
        results_message += texts["results_weak_topics"].format(topics=", ".join(weak_topics[:3]))
    
    await update.message.reply_text(results_message)

async def list_jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all active reminder jobs for debugging."""
    user_id = str(update.effective_user.id)
    
    try:
        import pytz
        from datetime import datetime
        
        # Jordan timezone
        jordan_tz = pytz.timezone('Asia/Amman')
        now_jordan = datetime.now(jordan_tz)
        
        job_name = f"reminder_{user_id}"
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        
        if current_jobs:
            job_info = []
            for job in current_jobs:
                next_run = job.next_t
                if next_run:
                    # Convert to Jordan timezone for display
                    next_run_jordan = next_run.astimezone(jordan_tz)
                    job_info.append(f"Job: {job.name}\nNext run: {next_run_jordan.strftime('%Y-%m-%d %H:%M:%S')} Jordan time")
                else:
                    job_info.append(f"Job: {job.name}\nNext run: Not scheduled")
            
            message = (
                f"📋 Active reminder jobs for you:\n\n" + 
                "\n\n".join(job_info) + 
                f"\n\nCurrent Jordan time: {now_jordan.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(
                f"❌ No active reminder jobs found for you.\n"
                f"Current Jordan time: {now_jordan.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
    except Exception as e:
        logger.error(f"Error in list_jobs_command: {str(e)}")
        await update.message.reply_text(f"❌ Error listing jobs: {str(e)}")

async def adaptive_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /adaptive_test command with nuclear session clearing."""
    user_id = str(update.effective_user.id)
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # NUCLEAR SESSION CLEARING - clear any remnants
    if user_id in user_data:
        user_info = user_data[user_id]
        session = user_info.get("current_test_session")
        
        if session:
            test_type = session.get("test_type", "")
            
            # FIXED: Clear completed adaptive test sessions
            if test_type == "Adaptive Test":
                # Check if adaptive test is complete (no remaining topics or empty topics)
                remaining_topics = session.get("remaining_topics", [])
                if not remaining_topics:
                    logger.warning(f"NUCLEAR: Clearing completed adaptive test session for user {user_id}")
                    user_info["current_test_session"] = None
                    if "active_session_ids" in user_info:
                        user_info["active_session_ids"] = {}
                    save_user_data()
            
            # If it's a completed reevaluation session, nuke it
            elif "Reevaluation" in test_type:
                questions = session.get("questions", [])
                current_index = session.get("current_question_index", 0)
                
                if current_index >= len(questions):
                    logger.warning(f"NUCLEAR: Clearing completed reevaluation in adaptive_test_command for user {user_id}")
                    user_info["current_test_session"] = None
                    if "active_session_ids" in user_info:
                        user_info["active_session_ids"] = {}
                    save_user_data()
    
    # Check if user already has an active test
    if has_active_test(user_id):
        await update.message.reply_text(
            f"{texts['active_session']}\n\n"
            f"If you're sure you don't have an active session, use /reset to clear any stuck sessions."
        )
        return
    
    # Show subject selection first
    keyboard = [
        [InlineKeyboardButton("CS211 DATA STRUCTURE", callback_data="subject_adaptive:CS211")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        texts["select_subject"],
        reply_markup=reply_markup
    )

async def set_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /set_reminder command for daily test notifications (using database)."""
    user_id = str(update.effective_user.id)
    
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Get user reminder settings from database
    reminder_settings = db_manager.get_user_reminder_settings(user_id)
    
    # Check if time argument is provided
    if context.args and len(context.args) > 0:
        time_arg = context.args[0].strip()
        
        # Clean the input to remove hidden Unicode characters (copy-paste fix)
        time_arg = time_arg.replace('\u200b', '').replace('\ufeff', '').replace('\u00a0', '').replace('\u2009', '').replace('\u202f', '')
        time_arg = ''.join(char for char in time_arg if char.isprintable() or char in ':0123456789')
        
        # Parse time - accept any H:M or HH:MM format
        try:
            if ':' in time_arg:
                hour_str, minute_str = time_arg.split(':', 1)
                hour = int(hour_str)
                minute = int(minute_str)
                
                # Basic validation
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    # Format time
                    formatted_time = f"{hour:02d}:{minute:02d}"
                    
                    # Update settings
                    reminder_settings["time"] = formatted_time
                    reminder_settings["enabled"] = True
                    reminder_settings["timezone"] = "Asia/Amman"
                    
                    # Save to database
                    db_manager.save_user_reminder_settings(user_id, reminder_settings)
                    
                    # Cancel and reschedule
                    cancel_daily_reminder(context, user_id)
                    schedule_daily_reminder(context, user_id, formatted_time)
                    
                    # Success message
                    success_msg = texts['reminder_time_updated'].format(formatted_time) + "\n\n" + texts['reminder_settings_saved']
                    await update.message.reply_text(success_msg)
                    return
                else:
                    # Hour/minute out of range
                    await update.message.reply_text("❌ Invalid time. Hours must be 0-23, minutes 0-59. " + texts['custom_time_instruction'])
                    return
            else:
                # No colon in time
                await update.message.reply_text("❌ Time must include ':' (e.g., 08:30). " + texts['custom_time_instruction'])
                return
        except ValueError:
            # Can't parse numbers
            await update.message.reply_text("❌ Invalid time format. " + texts['custom_time_instruction'])
            return
        except Exception as e:
            # Other errors
            logger.error(f"Error parsing time '{time_arg}' for user {user_id}: {str(e)}")
            await update.message.reply_text("❌ Error processing time. " + texts['custom_time_instruction'])
            return
    
    # Show reminder menu
    current_status = reminder_settings.get("enabled", False)
    
    keyboard = []
    
    if current_status:
        keyboard.append([InlineKeyboardButton(texts["disable_reminder"], callback_data="toggle_reminder")])
        keyboard.extend([
            [
                InlineKeyboardButton(texts["change_time_morning"], callback_data="set_time:09:00"),
                InlineKeyboardButton(texts["change_time_afternoon"], callback_data="set_time:14:00")
            ],
            [
                InlineKeyboardButton(texts["change_time_evening"], callback_data="set_time:19:00"),
                InlineKeyboardButton(texts["change_time_custom"], callback_data="set_time:custom")
            ]
        ])
    else:
        keyboard.append([InlineKeyboardButton(texts["enable_reminder"], callback_data="toggle_reminder")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Status message
    if current_status:
        status_text = texts["reminder_enabled"]
        
        if "time" in reminder_settings:
            job_name = f"reminder_{user_id}"
            active_jobs = context.job_queue.get_jobs_by_name(job_name)
            
            if active_jobs and len(active_jobs) > 0:
                next_job = active_jobs[0]
                if next_job.next_t:
                    jordan_tz = pytz.timezone('Asia/Amman')
                    next_run_jordan = next_job.next_t.astimezone(jordan_tz)
                    now_jordan = datetime.now(jordan_tz)
                    
                    if next_run_jordan > now_jordan:
                        if next_run_jordan.date() == now_jordan.date():
                            time_str = next_run_jordan.strftime('%H:%M')
                            today_text = texts['today_at'].format(time_str)
                            jordan_text = texts['jordan_time']
                            time_text = f"\n🕐 {texts['next_reminder'].format(today_text + ' ' + jordan_text)}"
                        else:
                            datetime_str = next_run_jordan.strftime('%Y-%m-%d %H:%M')
                            jordan_text = texts['jordan_time']
                            time_text = f"\n🕐 {texts['next_reminder'].format(datetime_str + ' ' + jordan_text)}"
                    else:
                        time_text = f"\n🕐 {texts['no_reminder_active']}"
                else:
                    time_text = f"\n🕐 {texts['no_reminder_active']}"
            else:
                time_text = f"\n🕐 {texts['no_reminder_active']}"
        else:
            time_text = f"\n🕐 {texts['no_reminder_active']}"
    else:
        status_text = texts["reminder_disabled"]
        time_text = f"\n🕐 {texts['no_reminder_active']}"
    
    final_message = texts['reminder_header'] + "\n\n" + status_text + time_text + "\n\n" + texts['reminder_description']
    await update.message.reply_text(final_message, reply_markup=reply_markup)

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /progress command to show user's quiz progress chart."""
    user_id = str(update.effective_user.id)
    
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    try:
        # Load progress data
        progress_data = load_progress_data(user_id)
        
        # Check if user has enough data
        if len(progress_data) < 2:
            if len(progress_data) == 0:
                message = texts.get("progress_no_data", "📊 You haven't completed any quizzes yet. Take a quiz first to see your progress!")
            else:
                message = texts.get("progress_need_more", "📊 You need to complete more quizzes to view your progress. Keep practicing!")
            
            await update.message.reply_text(message)
            return
        
        # Generate chart (no longer needs texts parameter)
        chart_buffer = generate_progress_chart(progress_data)
        
        # Calculate average score for additional info
        avg_score = sum(entry["score"] for entry in progress_data) / len(progress_data)
        avg_score = round(avg_score, 1)
        
        # Find latest score
        latest_score = progress_data[-1]["score"]
        
        # Create caption with stats
        caption = texts.get("progress_title", "📈 Your Quiz Progress") + "\n\n"
        caption += texts.get("progress_total", "📊 Total Quizzes: {}").format(len(progress_data)) + "\n"
        caption += texts.get("progress_average", "📈 Average Score: {}%").format(avg_score) + "\n"
        caption += texts.get("progress_latest", "🎯 Latest Score: {}%").format(latest_score) + "\n\n"
        
        # Add motivational message based on improved trend analysis
        if len(progress_data) >= 3:
            recent_scores = [entry["score"] for entry in progress_data[-3:]]
            latest_score = recent_scores[-1]
            average_recent = sum(recent_scores) / len(recent_scores)
            
            # Check if latest score is very low (below 30%)
            if latest_score < 30:
                caption += texts.get("progress_practice", "💪 Keep practicing to improve your scores!")
            # Check if recent average is low (below 40%) 
            elif average_recent < 40:
                caption += texts.get("progress_practice", "💪 Keep practicing to improve your scores!")
            # Check for improvement trend (last score better than average of first two)
            elif latest_score > (recent_scores[0] + recent_scores[1]) / 2:
                caption += texts.get("progress_improving", "📈 Great job! Your scores are improving!")
            # Check if consistently good (all scores above 60%)
            elif all(score >= 60 for score in recent_scores):
                caption += texts.get("progress_consistent", "📊 You're maintaining consistent performance!")
            else:
                caption += texts.get("progress_practice", "💪 Keep practicing to improve your scores!")
        else:
            caption += texts.get("progress_keep_going", "🚀 Keep taking quizzes to track your progress!")
        
        # Send the chart
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=chart_buffer,
            caption=caption
        )
        
        logger.info(f"Sent progress chart to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in progress_command for user {user_id}: {str(e)}")
        
        error_message = texts.get("progress_error", "❗ Sorry, there was an error generating your progress chart. Please try again later.")
        
        await update.message.reply_text(error_message)

async def contact_us_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /contact_us command."""
    user_id = str(update.effective_user.id)
    
    # Get user's language preference
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    contact_message = f"{texts['contact_us_header']}\n\n{texts['contact_us_message']}"
    
    await update.message.reply_text(contact_message, parse_mode='Markdown')

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: Dict) -> None:
    """Send a question to the user with DEBUGGING."""
    user_id = str(update.effective_user.id)
    logger.info(f"=== SEND QUESTION DEBUG ===")
    logger.info(f"send_question called for user {user_id}")
    
    # VERIFY SESSION EXISTS BEFORE SENDING
    if user_id in user_data:
        session = user_data[user_id].get("current_test_session")
        logger.info(f"Session exists when sending question: {session is not None}")
        if session:
            logger.info(f"Session type: {session.get('test_type')}")
            logger.info(f"Session debug ID: {session.get('debug_session_id', 'No ID')}")
    else:
        logger.warning(f"User {user_id} not in user_data when sending question!")
    
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    try:
        # Check if it's a valid question dictionary
        if not isinstance(question, dict):
            logger.error(f"Invalid question object: {question}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Invalid question format. Please try again or contact support."
            )
            return
        
        # Check required fields
        required_fields = ['topic', 'question', 'choices', 'correct_answer']
        missing_fields = [field for field in required_fields if field not in question]
        if missing_fields:
            logger.error(f"Question missing required fields: {missing_fields}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Question is missing required fields: {', '.join(missing_fields)}. Please try again."
            )
            return
        
        # Format the question message
        question_message = ""
        
        # Check if this is a mimic exam (to hide difficulty)
        is_mimic_exam = False
        if user_id in user_data:
            session = user_data[user_id].get("current_test_session")
            if session:
                test_type = session.get("test_type", "")
                is_mimic_exam = any(exam_type in test_type for exam_type in ["First Exam", "Second Exam", "Final Exam"])
        
        # Add topic and difficulty if available (but hide difficulty for mimic exams)
        if 'topic' in question:
            question_message += f"Topic: {question.get('topic', 'Unknown')}\n"
        if 'difficulty' in question and not is_mimic_exam:
            question_message += f"Difficulty: {question.get('difficulty', 'Unknown')}\n"
        
        # Add a separator and the question text
        question_message += f"\n{question.get('question', 'Question not available.')}\n\n"
        
        # Add choices
        choices = question.get('choices', {})
        if not choices:
            logger.error("Question has no choices")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Error: Question has no choices. Please try again."
            )
            return
            
        for option, text in choices.items():
            question_message += f"{option}. {text}\n"
        
        # ULTRA SIMPLIFIED callback prefix logic
        callback_prefix = "answer:"
        
        # Get the current session
        session = None
        if user_id in user_data:
            session = user_data[user_id].get("current_test_session")
        
        if session:
            test_type = session.get("test_type", "")
            logger.info(f"Current test type when creating callbacks: {test_type}")
            
            # Set the correct callback prefix based on test type
            if test_type == "Adaptive Test":
                callback_prefix = "adaptive_answer:"
            elif "reevaluation" in test_type.lower() or "Reevaluation" in test_type:
                callback_prefix = "reevaluation_answer:"
        
        logger.info(f"Using callback prefix: {callback_prefix}")
        
        # Create keyboard for answer options - ULTRA SIMPLE
        keyboard = []
        row = []
        
        for option in "ABCDE":
            if option in choices:
                # PURE SIMPLE CALLBACK - just prefix + letter
                callback_data = f"{callback_prefix}{option}"
                row.append(InlineKeyboardButton(option, callback_data=callback_data))
                logger.info(f"Created button: {option} -> {callback_data}")
        
        keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get the chat ID
        chat_id = update.effective_chat.id
        
        # Send the message
        await context.bot.send_message(
            chat_id=chat_id,
            text=question_message,
            reply_markup=reply_markup
        )
        logger.info(f"Question sent successfully with {len(row)} buttons")
        logger.info(f"=== SEND QUESTION COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Error in send_question: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"An error occurred while sending the question: {str(e)}. Please try again or use /reset."
            )
        except Exception as inner_e:
            logger.error(f"Failed to send error message: {str(inner_e)}")

async def show_navigation_options(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """
    Show navigation options with localized buttons after a test completion.
    
    Args:
        update: Telegram update object
        context: Telegram context object
        user_id: User ID
    """
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Create navigation keyboard with translated buttons
    keyboard = [
        [InlineKeyboardButton(texts["start_adaptive_button"], callback_data="start_adaptive_from_start")],
        [InlineKeyboardButton(texts["start_mimic_exam_button"], callback_data="start_mimic_incamp")],
        [InlineKeyboardButton(texts["return_to_main_menu"], callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the message with options
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=texts["what_next"],
        reply_markup=reply_markup
    )

async def show_adaptive_test_completion(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Show enhanced adaptive test completion message with recommendations for weak topics."""
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Load recommendations data
    recommendations = load_recommendations()
    
    # FIXED: Get the latest test from DATABASE, not just memory
    latest_test = None
    try:
        tests = db_manager.get_user_tests(user_id, limit=1)
        if tests and len(tests) > 0 and tests[0].get("test_type") == "Adaptive Test":
            latest_test = tests[0]
    except Exception as e:
        logger.error(f"Error retrieving latest test: {e}")
    
    # Fallback to memory if database fails
    if not latest_test:
        user_data_obj = get_user_data(user_id)
        adaptive_tests = user_data_obj.get("adaptive_tests", [])
        latest_test = adaptive_tests[0] if adaptive_tests else None
    
    # If still no test data, try to get from current session
    if not latest_test:
        user_data_obj = get_user_data(user_id)
        session = user_data_obj.get("current_test_session")
        if session and session.get("test_type") == "Adaptive Test":
            # Create a temporary test result from session data
            latest_test = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "topics_selected": session.get("topics", []),
                "weak_topics": session.get("weak_topics", []),
                "needs_more_training": session.get("needs_more_training", [])
            }
    
    # If still no test data, create minimal completion message
    if not latest_test:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🎓 {texts['test_completed']}\n\n📊 {texts['view_results']}\n🔄 {texts['start_another']}"
        )
        await show_navigation_options(update, context, user_id)
        # FIXED: Clear session from BOTH global cache and database
        if user_id in user_data:
            user_data[user_id]["current_test_session"] = None
        db_manager.clear_user_session(user_id)
        save_user_data()
        return
    
    # Build comprehensive completion message
    completion_message = (
        f"🎓 {texts['test_completed']}\n\n"
        f"📅 {texts['test_date'].format(latest_test.get('date', 'N/A'))}\n"
        f"📚 {texts['topics_tested'].format(', '.join(latest_test.get('topics_selected', [])))}\n\n"
    )
    
    # Add weak topics with recommendations
    weak_topics = latest_test.get("weak_topics", [])
    if weak_topics:
        completion_message += f"❗ {texts['topics_to_review']}: {', '.join(weak_topics)}\n\n"
        
        # Add recommendations for each weak topic
        for topic in weak_topics:
            topic_recommendations = format_topic_recommendations(topic, recommendations, texts, user_id)
            if topic_recommendations:
                completion_message += topic_recommendations + "\n"
    
    # Add needs more training topics with recommendations
    needs_training = latest_test.get("needs_more_training", [])
    if needs_training:
        completion_message += f"📈 {texts.get('topics_needing_advanced_practice', 'Topics needing advanced practice')}: {', '.join(needs_training)}\n\n"
        
        # Add recommendations for topics needing more training
        for topic in needs_training:
            topic_recommendations = format_topic_recommendations(topic, recommendations, texts, user_id)
            if topic_recommendations:
                completion_message += topic_recommendations + "\n"
    
    # Add final instructions
    completion_message += f"\n📊 {texts['view_results']}\n🔄 {texts['start_another']}"
    
    # Send single comprehensive message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=completion_message
    )
    
    # Create reevaluation buttons for weak topics
    if weak_topics:
        keyboard = []
        for topic in weak_topics:
            keyboard.append([InlineKeyboardButton(f"{texts['reevaluate_topic'].format(topic)}", callback_data=f"start_reevaluation:{topic}")])
        
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="💡 Would you like to take reevaluation tests on your weak topics?",
                reply_markup=reply_markup
            )

    # Create advanced reevaluation buttons for needs training topics  
    if needs_training:
        keyboard = []
        for topic in needs_training:
            keyboard.append([
                InlineKeyboardButton(f"📚 {texts.get('reevaluation_test', 'Reevaluation Test')}: {topic}", callback_data=f"start_reevaluation:{topic}")
            ])
            keyboard.append([
                InlineKeyboardButton(f"🔥 {texts.get('advanced_reevaluation_test', 'Advanced Reevaluation Test')}: {topic}", callback_data=f"start_advanced_reevaluation:{topic}")
            ])
        
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            # FIXED: Format the prompt with topic name(s)
            if len(needs_training) == 1:
                prompt_text = texts.get('advanced_practice_prompt', 'Would you like advanced practice?').format(needs_training[0])
            else:
                prompt_text = texts.get('advanced_practice_prompt', 'Would you like advanced practice?').format(', '.join(needs_training))
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prompt_text,
                reply_markup=reply_markup
            )
    
    # Always show navigation options at the end
    await show_navigation_options(update, context, user_id)
    
    # FIXED: Clear session from BOTH global cache and database
    if user_id in user_data:
        user_data[user_id]["current_test_session"] = None
    else:
        # Ensure user exists in global cache with cleared session
        user_data[user_id] = get_user_data(user_id)
        user_data[user_id]["current_test_session"] = None
        
    db_manager.clear_user_session(user_id)
    save_user_data()
    logger.info(f"Cleared adaptive test session for user {user_id} after completion message")

async def show_exam_completion(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, test_results: Dict) -> None:
    """Show a detailed exam completion summary with all questions and explanations.
    
    Located in: simple_bot.py (standalone function)
    
    Args:
        update: Telegram update object
        context: Telegram context object
        user_id: User ID
        test_results: Dictionary containing test results
    """
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    try:
        logger.info(f"Showing exam completion for user {user_id}, score: {test_results.get('score', 'Unknown')}")
        
        # Safeguard: Ensure the test is properly recorded in user's history
        # This is needed because sometimes the normal completion flow might fail
        user_info = get_user_data(user_id)
        
        # Check if this test result is already in user's history
        # If not, add it manually
        is_already_recorded = False
        for test in user_info.get("tests", []):
            # Check if same test type, date, and score
            if (test.get("test_type") == test_results.get("test_type") and
                test.get("score") == test_results.get("score") and
                test.get("date") == test_results.get("date")):
                is_already_recorded = True
                break
        
        if not is_already_recorded:
            # Add timestamp to test_results if not present
            if "time" not in test_results:
                test_results["time"] = datetime.now().strftime("%H:%M")
            
            # Ensure tests array exists
            if "tests" not in user_info:
                user_info["tests"] = []
                
            # Add to tests history (limited to last 5)
            user_info["tests"].insert(0, test_results)
            if len(user_info["tests"]) > 5:
                user_info["tests"] = user_info["tests"][:5]
            
            # Update weak topic pool
            if "weak_topic_pool" not in user_info:
                user_info["weak_topic_pool"] = []
                
            # Add new weak topics to the pool (avoid duplicates)
            for topic in test_results.get("weak_topics", []):
                if topic not in user_info["weak_topic_pool"]:
                    user_info["weak_topic_pool"].append(topic)
            
            # Save user data
            save_user_data()
            logger.info(f"Safeguard: Manually recorded test result for user {user_id}")
        
        # CRITICAL FIX: Store exam results in database as user session backup
        backup_data = {
            "type": "exam_results_backup",
            "test_results": test_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        db_manager.save_user_session(f"{user_id}_exam_backup", backup_data)
        
        # Also store in memory cache for immediate access
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id)
        user_data[user_id]["last_exam_results"] = test_results
        save_user_data()
        
        # Format completion message
        completion_message = (
            f"{texts['exam_complete']}\n\n"
            f"{texts['your_score'].format(test_results.get('score', 'N/A'))}\n\n"
        )
        
        # Add weak topics if any
        if test_results.get('weak_topics'):
            completion_message += (
                f"{texts['topics_to_review_header']}\n"
                f"- {', '.join(test_results['weak_topics'])}\n\n"
            )
        
        # Send initial summary
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=completion_message
        )
        
        # Get the questions from test_results
        questions = test_results.get('questions', [])
        answers = test_results.get('answers', [])
        
        if not questions:
            logger.warning(f"No questions found in test_results for user {user_id}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["no_detailed_questions"]
            )
        else:
            # Ask user if they want to see detailed explanations
            keyboard = [
                [InlineKeyboardButton(texts["show_detailed_button"], callback_data="show_detailed_results")],
                [InlineKeyboardButton(texts["show_incorrect_button"], callback_data="show_incorrect_only")],
                [InlineKeyboardButton(texts["skip_details_button"], callback_data="skip_exam_details")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["review_questions_prompt"],
                reply_markup=reply_markup
            )
        
        # Show navigation options with localized buttons
        await show_navigation_options(update, context, user_id)
        
    except Exception as e:
        logger.error(f"Error showing exam completion: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Send a simplified completion message in case of error
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=texts["exam_complete_simple"].format(test_results.get('score', 'N/A'))
        )
        
        # Still try to show navigation options even if there was an error
        await show_navigation_options(update, context, user_id)

async def handle_detailed_results_request(update: Update, context: ContextTypes.DEFAULT_TYPE, show_only_incorrect: bool = False) -> None:
    """Handle request to show detailed exam results."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # CRITICAL FIX: Try multiple sources to get test results
    test_results = None
    
    # 1. Try from memory cache first
    user_data_obj = get_user_data(user_id)
    test_results = user_data_obj.get("last_exam_results")
    
    # 2. If not in cache, try from database backup
    if not test_results:
        try:
            backup_data = db_manager.load_user_session(f"{user_id}_exam_backup")
            if backup_data and backup_data.get("type") == "exam_results_backup":
                test_results = backup_data.get("test_results")
                logger.info(f"Retrieved exam results from database backup for user {user_id}")
        except Exception as e:
            logger.error(f"Error loading exam backup: {e}")
    
    # 3. Last resort: try from recent test history
    if not test_results:
        recent_tests = db_manager.get_user_tests(user_id, limit=1)
        if recent_tests and len(recent_tests) > 0:
            recent_test = recent_tests[0]
            # Check if it's a recent exam (within last 10 minutes)
            try:
                test_time = datetime.strptime(f"{recent_test['date']} {recent_test['time']}", "%Y-%m-%d %H:%M")
                time_diff = datetime.now() - test_time
                if time_diff.total_seconds() < 600:  # 10 minutes
                    test_results = recent_test
                    logger.info(f"Retrieved exam results from recent test history for user {user_id}")
            except Exception as e:
                logger.error(f"Error parsing test time: {e}")
    
    if not test_results:
        await query.edit_message_text("Sorry, the test results are no longer available.")
        return
    
    # Get the questions and answers
    questions = test_results.get('questions', [])
    
    # For regular exams, answers are stored differently than for adaptive tests
    answers = []
    if "answers" in test_results:
        answers = test_results["answers"]
    else:
        # Try to reconstruct answers from correct_count
        correct_count = test_results.get("correct_count", 0)
        for i in range(len(questions)):
            if i < correct_count:
                answers.append(questions[i]["correct_answer"])
            else:
                # For incorrect answers, we don't know what the user selected, so use a placeholder
                answers.append("Unknown")
    
    # Count incorrect answers to see if we need to show anything
    incorrect_count = sum(1 for i, q in enumerate(questions) if i < len(answers) and answers[i] != q.get("correct_answer"))
    
    if show_only_incorrect and incorrect_count == 0:
        await query.edit_message_text(texts["congratulations"])
        
        # Add navigation options here as well
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📊 {texts['view_results']}\n"
                 f"🔄 {texts['start_another']}\n"
                 f"🏠 Use /start to return to the main menu."
        )
        return
    
    # Send detailed explanations in chunks to avoid message size limits
    chunk_size = 3  # Number of questions per message
    
    # Filter questions if only showing incorrect
    if show_only_incorrect:
        question_indices = [i for i, q in enumerate(questions) if i < len(answers) and answers[i] != q.get("correct_answer")]
    else:
        question_indices = list(range(len(questions)))
    
    total_chunks = (len(question_indices) + chunk_size - 1) // chunk_size
    
    # Update the original message
    await query.edit_message_text(
        f"📚 {'Incorrect answers' if show_only_incorrect else 'Detailed results'} "
        f"will be sent in {total_chunks} messages..."
    )
    
    for chunk_index in range(total_chunks):
        start_idx = chunk_index * chunk_size
        end_idx = min(start_idx + chunk_size, len(question_indices))
        
        detailed_message = f"📝 {'Incorrect answers' if show_only_incorrect else 'Results'} "
        detailed_message += f"({chunk_index+1}/{total_chunks}):\n\n"
        
        for i in range(start_idx, end_idx):
            q_idx = question_indices[i]
            question = questions[q_idx]
            
            user_answer = "No answer"
            if q_idx < len(answers):
                user_answer = answers[q_idx]
            
            correct_answer = question.get('correct_answer', "Unknown")
            is_correct = user_answer == correct_answer
            
            # Format question review
            question_review = (
                f"{q_idx+1}. {'✅' if is_correct else '❌'} {question.get('question', 'No question')}\n"
                f"   Your answer: {user_answer}\n"
                f"   ✅ Correct: {correct_answer}\n"
            )
            
            # Add explanation only for incorrect answers to save space
            if not is_correct or not show_only_incorrect:
                explanation = question.get('explanation', 'No explanation available.')
                # Truncate long explanations
                if len(explanation) > 200:
                    explanation = explanation[:197] + "..."
                question_review += f"   📚 Explanation: {explanation}\n"
            
            question_review += "\n"
            
            # Add to the message
            detailed_message += question_review
        
        # Send the chunk
        if len(detailed_message) > 4000:
            # Split into smaller messages if needed
            parts = [detailed_message[i:i+4000] for i in range(0, len(detailed_message), 4000)]
            for part in parts:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=part
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=detailed_message
            )
    
    # Send navigation options AFTER all results are sent
    # This message will be more visible and accessible to the user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"📊 {texts['view_results']}\n"
             f"🔄 {texts['start_another']}\n"
             f"🏠 Use /start to return to the main menu."
    )
    
    # If we showed only incorrect answers, offer to see all
    if show_only_incorrect:
        keyboard = [
            [InlineKeyboardButton("Show All Results", callback_data="show_detailed_results")],
            [InlineKeyboardButton("Close", callback_data="skip_exam_details")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Would you like to see all questions including the correct ones?",
            reply_markup=reply_markup
        )
        
async def handle_results_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle results button press from callbacks."""
    user_id = str(update.effective_user.id)
    
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    user_info = get_user_data(user_id)
    
    # Get test results
    test_results = user_info.get("tests", [])
    
    if not test_results:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=texts["results_empty"]
        )
        return
        
    # Format results message
    results_message = texts["results_header"] + "\n\n"
    
    for i, test in enumerate(test_results):
        # Format the weak topics string
        weak_topics_str = ", ".join(test.get('weak_topics', [])) if test.get('weak_topics', []) else texts["results_no_weak_topics"]
        
        # Add time if available, otherwise just show date
        date_str = test.get('date', 'N/A')
        time_str = test.get('time', '')
        if time_str:
            date_str = f"{date_str} {time_str}"
        
        # Format this entry using the template from translations
        # Ensure the exact test_type is used (First Exam, Second Exam, Final Exam)
        entry = texts["results_test_entry"].format(
            index=i+1,
            test_type=test.get('test_type', 'Test'),
            date=date_str,
            score=test.get('score', 'N/A'),
            weak_topics=weak_topics_str
        )
        results_message += entry
    
    # Get overall weak topics
    weak_topics = user_info.get("weak_topic_pool", [])
    if weak_topics:
        results_message += texts["results_weak_topics"].format(topics=", ".join(weak_topics[:3]))
    
    # Send the message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=results_message
    )

async def handle_advanced_reevaluation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle advanced reevaluation callback with SIMPLE session management"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    all_mcqs = context.bot_data.get("all_mcqs", [])
    
    if callback_data.startswith("start_advanced_reevaluation:"):
        try:
            topic = callback_data.replace("start_advanced_reevaluation:", "")
            logger.info(f"Starting advanced reevaluation for topic {topic} for user {user_id}")
            
            # Send a message to show we're starting
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔥 Starting advanced reevaluation for {topic}..."
            )
            
            # Start advanced reevaluation test
            result = start_advanced_reevaluation_test(user_id, topic, all_mcqs)
            
            if "error" in result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ {result['error']}"
                )
                return
            
            # Show advanced reevaluation test intro
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔥 **ADVANCED REEVALUATION TEST: {topic}**\n\nThis test contains only HARD questions to challenge your mastery.\nPrepare for advanced-level problems!"
            )
            
            # Send first question
            if "first_question" in result:
                await send_question(update, context, result["first_question"])
            else:
                logger.error(f"No first_question in advanced reevaluation result: {result}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Error: Could not start advanced reevaluation test. Please use /reset and try again."
                )
        except Exception as e:
            logger.error(f"Error starting advanced reevaluation for user {user_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❗ An error occurred while starting the advanced reevaluation test. Please try again or use /reset to clear your session."
            )

async def handle_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle reminder-related callback queries (using database)."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Get reminder settings from database
    reminder_settings = db_manager.get_user_reminder_settings(user_id)
    
    if callback_data == "toggle_reminder":
        current_status = reminder_settings.get("enabled", False)
        
        if current_status:
            # Disable reminders
            reminder_settings["enabled"] = False
            if "time" in reminder_settings:
                del reminder_settings["time"]
            
            db_manager.save_user_reminder_settings(user_id, reminder_settings)
            cancel_daily_reminder(context, user_id)
            
            status_message = f"{texts['reminder_turned_off']}\n{texts['notifications_deleted']}"
            reply_markup = None
            
        else:
            # Enable reminders
            reminder_settings["enabled"] = True
            db_manager.save_user_reminder_settings(user_id, reminder_settings)
            
            status_message = texts["reminder_turned_on"]
            keyboard = [
                [InlineKeyboardButton(texts["disable_reminder"], callback_data="toggle_reminder")],
                [
                    InlineKeyboardButton(texts["change_time_morning"], callback_data="set_time:09:00"),
                    InlineKeyboardButton(texts["change_time_afternoon"], callback_data="set_time:14:00")
                ],
                [
                    InlineKeyboardButton(texts["change_time_evening"], callback_data="set_time:19:00"),
                    InlineKeyboardButton(texts["change_time_custom"], callback_data="set_time:custom")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{status_message}\n\n{texts['reminder_settings_saved']}",
            reply_markup=reply_markup
        )
        
    elif callback_data.startswith("set_time:"):
        # Check if reminders are enabled
        if not reminder_settings.get("enabled", False):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["enable_reminders_first"]
            )
            return
        
        time_value = callback_data.replace("set_time:", "")
        
        if time_value == "custom":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["custom_time_instruction"]
            )
            return
        
        # Update the time in database
        reminder_settings["time"] = time_value
        reminder_settings["timezone"] = "Asia/Amman"
        
        db_manager.save_user_reminder_settings(user_id, reminder_settings)
        
        # Cancel existing jobs and schedule new one
        cancel_daily_reminder(context, user_id)
        schedule_daily_reminder(context, user_id, time_value)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{texts['reminder_time_updated'].format(time_value)}\n\n{texts['reminder_settings_saved']}"
        )

def schedule_daily_reminder(context: ContextTypes.DEFAULT_TYPE, user_id: str, time_str: str) -> None:
    """Schedule a one-time reminder for the user that disables after triggering."""
    try:
        # Parse time string (HH:MM format)
        hour, minute = map(int, time_str.split(':'))
        
        # Create job name
        job_name = f"reminder_{user_id}"
        
        # Remove existing job if any
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
            logger.info(f"Removed existing reminder job for user {user_id}")
        
        # Also remove any existing once jobs
        once_jobs = context.job_queue.get_jobs_by_name(f"{job_name}_once")
        for job in once_jobs:
            job.schedule_removal()
            logger.info(f"Removed existing once reminder job for user {user_id}")
        
        # Jordan timezone
        jordan_tz = pytz.timezone('Asia/Amman')
        
        # Get current time in Jordan timezone
        now_jordan = datetime.now(jordan_tz)
        
        # Create target time for TODAY
        target_time_today = now_jordan.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Check if target time is in the future TODAY
        if target_time_today > now_jordan:
            # Schedule for TODAY if time hasn't passed yet
            next_run_jordan = target_time_today
            logger.info(f"Scheduling for TODAY - time {time_str} hasn't passed yet")
        else:
            # Schedule for TOMORROW if time already passed today
            next_run_jordan = target_time_today + timedelta(days=1)
            logger.info(f"Scheduling for TOMORROW - time {time_str} already passed today")
        
        # Schedule as a one-time job that will disable itself after execution
        context.job_queue.run_once(
            send_daily_reminder,
            when=next_run_jordan,
            data=user_id,
            name=job_name
        )
        
        logger.info(f"Scheduled ONE-TIME reminder for user {user_id} at {time_str} Jordan time")
        logger.info(f"Reminder will be sent at: {next_run_jordan.strftime('%Y-%m-%d %H:%M:%S')} Jordan time")
        logger.info(f"Current Jordan time: {now_jordan.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Reminder will auto-disable after sending")
        
    except Exception as e:
        logger.error(f"Error scheduling reminder for user {user_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def cancel_daily_reminder(context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Cancel daily reminder for the user and ACTUALLY remove all related jobs."""
    try:
        job_name = f"reminder_{user_id}"
        
        logger.info(f"STARTING cancellation for user {user_id}")
        
        # Get ALL jobs before removal
        all_jobs = list(context.job_queue.jobs())
        logger.info(f"Total jobs in queue: {len(all_jobs)}")
        
        # Find jobs to remove
        jobs_to_remove = []
        for job in all_jobs:
            should_remove = False
            
            # Check by name
            if job.name == job_name:
                should_remove = True
                logger.info(f"Found job by exact name: {job.name}")
            
            # Check by user ID in name
            elif job.name and user_id in str(job.name) and "reminder" in str(job.name).lower():
                should_remove = True
                logger.info(f"Found job by pattern: {job.name}")
            
            # Check by callback function and data
            elif (hasattr(job, 'data') and 
                  str(job.data) == str(user_id) and 
                  hasattr(job, 'callback')):
                try:
                    # Import the function to compare
                    if job.callback.__name__ == 'send_daily_reminder':
                        should_remove = True
                        logger.info(f"Found job by callback: {job.name}")
                except:
                    pass
            
            if should_remove:
                jobs_to_remove.append(job)
        
        logger.info(f"Found {len(jobs_to_remove)} jobs to remove: {[j.name for j in jobs_to_remove]}")
        
        # ACTUALLY REMOVE THE JOBS
        removed_count = 0
        for job in jobs_to_remove:
            try:
                # Method 1: Disable immediately
                if hasattr(job, 'enabled'):
                    job.enabled = False
                
                # Method 2: Schedule removal
                job.schedule_removal()
                
                # Method 3: FORCE removal from internal job list
                try:
                    if hasattr(context.job_queue, '_jobs') and job in context.job_queue._jobs:
                        context.job_queue._jobs.remove(job)
                        logger.info(f"FORCE REMOVED from _jobs: {job.name}")
                except Exception as force_error:
                    logger.error(f"Force removal failed: {force_error}")
                
                # Method 4: Try to stop the job if it has a timer
                try:
                    if hasattr(job, '_job') and job._job:
                        job._job.cancel()
                        logger.info(f"Cancelled timer for: {job.name}")
                except:
                    pass
                
                removed_count += 1
                logger.info(f"REMOVED job: {job.name}")
                
            except Exception as remove_error:
                logger.error(f"Error removing job {job.name}: {remove_error}")
        
        # VERIFY REMOVAL
        remaining_jobs = list(context.job_queue.jobs())
        user_jobs_remaining = [job for job in remaining_jobs 
                              if job.name and user_id in str(job.name) and "reminder" in str(job.name).lower()]
        
        logger.info(f"RESULT: Removed {removed_count} jobs, {len(user_jobs_remaining)} jobs still remain")
        
        if user_jobs_remaining:
            logger.error(f"FAILED TO REMOVE: {[j.name for j in user_jobs_remaining]}")
            
            # Recreate the entire job list without our jobs
            try:
                if hasattr(context.job_queue, '_jobs'):
                    clean_jobs = []
                    for job in context.job_queue._jobs:
                        keep_job = True
                        if job.name and user_id in str(job.name) and "reminder" in str(job.name).lower():
                            keep_job = False
                            logger.info(f"NUCLEAR: Excluding {job.name}")
                        elif (hasattr(job, 'data') and str(job.data) == str(user_id) and 
                              hasattr(job, 'callback') and job.callback.__name__ == 'send_daily_reminder'):
                            keep_job = False
                            logger.info(f"NUCLEAR: Excluding by callback {job.name}")
                        
                        if keep_job:
                            clean_jobs.append(job)
                    
                    context.job_queue._jobs = clean_jobs
                    logger.info(f"NUCLEAR: Rebuilt job queue with {len(clean_jobs)} jobs")
            except Exception as nuclear_error:
                logger.error(f"Nuclear option failed: {nuclear_error}")
        else:
            logger.info(f"SUCCESS: All reminder jobs removed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Critical error in cancel_daily_reminder: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily reminder to user."""
    user_id = context.job.data
    
    try:
        # Jordan timezone for logging
        jordan_tz = pytz.timezone('Asia/Amman')
        now_jordan = datetime.now(jordan_tz)
        
        logger.info(f"Attempting to send daily reminder to user {user_id} at {now_jordan.strftime('%Y-%m-%d %H:%M:%S')} Jordan time")
        
        # Get user's language
        lang = get_user_language(user_id)
        texts = TEXTS[lang]
        
        # Check if user still has reminders enabled - USE DATABASE instead of user_data
        reminder_settings = db_manager.get_user_reminder_settings(user_id)
        if not reminder_settings.get("enabled", False):
            # User disabled reminders, cancel the job
            logger.info(f"User {user_id} has disabled reminders, cancelling job")
            cancel_daily_reminder(context, user_id)
            return
        
        # Create reminder message with action buttons including disable
        keyboard = [
            [InlineKeyboardButton(texts["start_adaptive_button"], callback_data="start_adaptive_from_start")],
            [InlineKeyboardButton(texts["start_mimic_exam_button"], callback_data="start_mimic_incamp")],
            [InlineKeyboardButton(texts["disable_reminder"], callback_data="toggle_reminder")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get user's weak topics for personalized message - USE DATABASE
        weak_topics = db_manager.get_weak_topics(user_id)
        if weak_topics:
            topic_suggestion = texts["reminder_weak_topics"].format(", ".join(weak_topics[:3]))
        else:
            topic_suggestion = texts["reminder_general_suggestion"]
        
        reminder_message = f"{texts['daily_reminder_header']}\n\n{topic_suggestion}\n\n{texts['daily_reminder_footer']}"
        
        await context.bot.send_message(
            chat_id=user_id,
            text=reminder_message,
            reply_markup=reply_markup
        )
        
        logger.info(f"Successfully sent daily reminder to user {user_id} at {now_jordan.strftime('%Y-%m-%d %H:%M:%S')} Jordan time")
        
        # Remove the time setting so status shows "no active reminder"
        reminder_settings["enabled"] = True  # Keep enabled but remove time
        if "time" in reminder_settings:
            del reminder_settings["time"]
        
        # Save updated settings to database
        db_manager.save_user_reminder_settings(user_id, reminder_settings)
        
        # Cancel/remove only this job
        cancel_daily_reminder(context, user_id)
        
        logger.info(f"Deleted reminder job for user {user_id} - reminders still enabled but no active reminder")
        
    except Exception as e:
        logger.error(f"Error sending daily reminder to user {user_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Still delete the reminder even if sending failed
        try:
            reminder_settings = db_manager.get_user_reminder_settings(user_id)
            if "time" in reminder_settings:
                del reminder_settings["time"]
            db_manager.save_user_reminder_settings(user_id, reminder_settings)
            cancel_daily_reminder(context, user_id)
            logger.info(f"Deleted reminder for user {user_id} after error")
        except Exception as delete_error:
            logger.error(f"Error deleting reminder after failure: {delete_error}")

def restore_reminder_jobs(application) -> None:
    """Restore reminder jobs for all users who have reminders enabled."""
    try:
        # Jordan timezone
        jordan_tz = pytz.timezone('Asia/Amman')
        now_jordan = datetime.now(jordan_tz)
        
        # Load user data to check for enabled reminders
        global user_data
        if not user_data:
            load_user_data()
        
        restored_count = 0
        
        for user_id, data in user_data.items():
            reminder_settings = data.get("reminder_settings", {})
            
            if reminder_settings.get("enabled", False):
                reminder_time = reminder_settings.get("time", "09:00")
                
                try:
                    # Schedule the reminder job
                    hour, minute = map(int, reminder_time.split(':'))
                    job_name = f"reminder_{user_id}"
                    
                    # Remove any existing job for this user
                    current_jobs = application.job_queue.get_jobs_by_name(job_name)
                    for job in current_jobs:
                        job.schedule_removal()
                    
                    # Schedule new job with Jordan timezone
                    application.job_queue.run_daily(
                        send_daily_reminder,
                        time=time(hour=hour, minute=minute, tzinfo=jordan_tz),
                        data=user_id,
                        name=job_name
                    )
                    
                    restored_count += 1
                    logger.info(f"Restored reminder for user {user_id} at {reminder_time} Jordan time")
                    
                except Exception as e:
                    logger.error(f"Error restoring reminder for user {user_id}: {str(e)}")
        
        logger.info(f"Restored {restored_count} reminder jobs on startup")
        logger.info(f"Current Jordan time: {now_jordan.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"Error restoring reminder jobs: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()  # Answer the callback query to stop the loading indicator
    
    user_id = str(update.effective_user.id)
    callback_data = query.data
    
    # Get language preference
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Get mcqs from context
    all_mcqs = context.bot_data.get("all_mcqs", [])
    
    # Show language selection list
    if callback_data == "show_languages":
        # Show language options as a list
        keyboard = [
            [InlineKeyboardButton("English 🇬🇧", callback_data="set_language:en")],
            [InlineKeyboardButton("العربية 🇸🇦", callback_data="set_language:ar")],
            [InlineKeyboardButton("Back", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Please select your preferred language:\n\n"
            "يرجى اختيار لغتك المفضلة:",
            reply_markup=reply_markup
        )
        return
    
    # Set language on direct language selection
    elif callback_data.startswith("set_language:"):
        selected_lang = callback_data.replace("set_language:", "")
        if selected_lang in ["en", "ar"]:
            set_user_language(user_id, selected_lang)
            
            # Get updated texts in the selected language
            texts = TEXTS[selected_lang]
            
            # Update welcome message with selected language 
            welcome_message = (
                f"👋 {texts['hello']} {update.effective_user.first_name}! {texts['welcome_to_bot']}\n\n"
                f"{texts['bot_description']}\n\n"
                f"{texts['language_selection']}\n"
                f"To change the language, click below / لتغيير اللغة، انقر أدناه\n\n"
                f"📋 {texts['commands_header']}:\n"
                f"/subjects - {texts['subjects_command']}\n"
                f"/topics - {texts['topics_command']}\n"
                f"/adaptive_test - {texts['adaptive_test_command']}\n"
                f"/mimic_incamp_exam - {texts['mimic_exam_command']}\n"
                f"/results - {texts['results_command']}\n"
                f"/progress - {texts.get('progress_command', 'View your quiz progress chart')}\n"
                f"/set_reminder - {texts['set_reminder_command']}\n"
                f"/reset - {texts['reset_command']}\n"
                f"/contact_us - {texts['contact_us_command']}\n\n"
                f"✏️ {texts['adaptive_test_description']}"
            )
            
            # Create language selection buttons in a list format
            keyboard = [
                [InlineKeyboardButton("Select Language / اختر اللغة", callback_data="show_languages")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send welcome message in the selected language
            await query.edit_message_text(welcome_message, reply_markup=reply_markup)
        return

    # Handle subject selection
    elif callback_data.startswith("select_subject:"):
        subject = callback_data.replace("select_subject:", "")
        if subject == "CS211":
            # Show CS211 options
            keyboard = [
                [InlineKeyboardButton(f"📚 {texts.get('topics_command', 'View Topics')}", callback_data="subject_topics:CS211")],
                [InlineKeyboardButton(f"🧠 {texts.get('adaptive_test_command', 'Adaptive Test')}", callback_data="subject_adaptive:CS211")],
                [InlineKeyboardButton(f"🎯 {texts.get('mimic_exam_command', 'Mimic Exam')}", callback_data="subject_mimic:CS211")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📖 CS211 - Data Structures\n\n"
                f"Choose what you'd like to do with this subject:",
                reply_markup=reply_markup
            )
        return

    # CRITICAL FIX: Add stale session clearing for adaptive test buttons (same as mimic exam)
    elif callback_data in ["start_adaptive_from_start", "start_adaptive_from_topics", "subject_adaptive:CS211"]:
        # Add the same stale session clearing logic as mimic exam
        if user_id in user_data:
            session = user_data[user_id].get("current_test_session")
            if session:
                # Check if session is stale or broken
                is_valid_session = True
                
                if "questions" in session and "current_question_index" in session:
                    questions = session.get("questions", [])
                    current_index = session.get("current_question_index", 0)
                    
                    if not questions or current_index >= len(questions):
                        is_valid_session = False
                        logger.warning(f"Found stale session for user {user_id}. Forcing reset.")
                
                # Detect other kinds of broken sessions
                if session.get("test_type") and not isinstance(session.get("test_type"), str):
                    is_valid_session = False
                
                # Force reset stale or invalid sessions
                if not is_valid_session:
                    user_data[user_id]["current_test_session"] = None
                    save_user_data()
                    logger.info(f"Cleared stale session for user {user_id}")

    # Handle subject selection for adaptive test
    if callback_data.startswith("subject_adaptive:"):
        subject = callback_data.replace("subject_adaptive:", "")
        if subject == "CS211":
            # Check if user already has an active test
            if has_active_test(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=texts["active_session"]
                )
                return
                
            # Initialize selection for this user
            user_selections[user_id] = {
                "selected_topics": [],
                "all_topics": TOPICS
            }
            
            # Create topic selection buttons
            keyboard = []
            for topic in TOPICS:
                keyboard.append([
                    InlineKeyboardButton(f"☐ {topic}", callback_data=f"select_topic:{topic}")
                ])
            
            # Add control buttons at the bottom
            keyboard.append([
                InlineKeyboardButton(texts["select_all"], callback_data="select_all"),
                InlineKeyboardButton(texts["clear_all"], callback_data="clear_all")
            ])
            keyboard.append([
                InlineKeyboardButton(texts["start_test"], callback_data="start_test")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                texts["welcome_adaptive"],
                reply_markup=reply_markup
            )
        return

    # Handle subject selection for topics command
    elif callback_data.startswith("subject_topics:"):
        subject = callback_data.replace("subject_topics:", "")
        if subject == "CS211":
            # Proceed with original topics logic
            topics_message = texts["topics_header"] + "\n\n" + "\n".join([f"• {topic}" for topic in TOPICS])
            
            keyboard = [
                [InlineKeyboardButton(texts["start_adaptive_from_topics"], callback_data="start_adaptive_from_topics")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            reset_message = texts["topics_reset"] if user_data.get(user_id, {}).get("current_test_session") else ""
            
            await query.edit_message_text(
                topics_message + reset_message,
                reply_markup=reply_markup
            )
        return

    # Handle subject selection for mimic exam
    elif callback_data.startswith("subject_mimic:"):
        subject = callback_data.replace("subject_mimic:", "")
        if subject == "CS211":
            # Proceed with original mimic exam logic
            keyboard = [
                [InlineKeyboardButton(texts["first_exam_desc"], callback_data="start_first_exam")],
                [InlineKeyboardButton(texts["second_exam_desc"], callback_data="second_exam_options")],
                [InlineKeyboardButton(texts["final_exam_desc"], callback_data="final_exam_options")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"{texts['mimic_exam_header']}\n\n"
                f"{texts['mimic_exam_intro']}\n\n"
                f"{texts['first_exam_desc']}\n"
                f"{texts['second_exam_desc']}\n"
                f"{texts['final_exam_desc']}\n\n"
                f"{texts['exam_experience_note']}",
                reply_markup=reply_markup
            )
        return
    
    # Handle reminder callbacks
    elif callback_data == "toggle_reminder" or callback_data.startswith("set_time:"):
        await handle_reminder_callback(update, context, callback_data)
        return
    
    # Handle back to start 
    elif callback_data == "back_to_start":
        # Get current language
        lang = get_user_language(user_id)
        texts = TEXTS[lang]
        
        # Get user's first name
        user = update.effective_user
        
        # Regenerate welcome message with progress command and contact us
        welcome_message = (
            f"👋 {texts['hello']} {user.first_name}! {texts['welcome_to_bot']}\n\n"
            f"{texts['bot_description']}\n\n"
            f"{texts['language_selection']}\n"
            f"To change the language, click below / لتغيير اللغة، انقر أدناه\n\n"
            f"📋 {texts['commands_header']}:\n"
            f"/subjects - {texts['subjects_command']}\n"
            f"/topics - {texts['topics_command']}\n"
            f"/adaptive_test - {texts['adaptive_test_command']}\n"
            f"/mimic_incamp_exam - {texts['mimic_exam_command']}\n"
            f"/results - {texts['results_command']}\n"
            f"/progress - {texts.get('progress_command', 'View your quiz progress chart')}\n"
            f"/set_reminder - {texts['set_reminder_command']}\n"
            f"/reset - {texts['reset_command']}\n"
            f"/contact_us - {texts['contact_us_command']}\n\n"
            f"✏️ {texts['adaptive_test_description']}"
        )
        
        # Create language selection buttons in a list format
        keyboard = [
            [InlineKeyboardButton("Select Language / اختر اللغة", callback_data="show_languages")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)
        return
    
    # Handle direct start from language selection
    elif callback_data == "start_adaptive_from_start":
        try:
            # Before calling adaptive_test_command, make sure user doesn't have active session
            if has_active_test(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=texts["active_session"]
                )
                return
                
            # Show subject selection instead of going directly to topic selection
            keyboard = [
                [InlineKeyboardButton("CS211 DATA STRUCTURE", callback_data="subject_adaptive:CS211")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                texts["select_subject"],
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error starting adaptive test: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❗ An error occurred when starting the adaptive test: {str(e)}\n\n"
                     f"Please try again or use /reset if the problem persists."
            )
        return
        
    # Handle mimic in-camp exam selection from start menu
    elif callback_data == "start_mimic_incamp":
        # Show subject selection instead of going directly to exam options
        keyboard = [
            [InlineKeyboardButton("CS211 DATA STRUCTURE", callback_data="subject_mimic:CS211")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            texts["select_subject"],
            reply_markup=reply_markup
        )
        return
    
    # Handle original start_command language selection
    elif callback_data == "start_adaptive_from_topics":
        try:
            # Before attempting to start, check if user has active session
            if has_active_test(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=texts["active_session"]
                )
                return
                
            # Show subject selection instead of going directly to topic selection
            keyboard = [
                [InlineKeyboardButton("CS211 DATA STRUCTURE", callback_data="subject_adaptive:CS211")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                texts["select_subject"],
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error starting adaptive test from topics: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❗ An error occurred: {str(e)}\n\nPlease try again or use /reset."
            )
        return
    
    # Process exam options for first exam
    elif callback_data == "start_first_exam":
        try:
            # Log action and available data
            logger.info(f"start_first_exam callback received from user {user_id}")
            
            # Check if user has an active test session - with option to reset
            if has_active_test(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{texts['active_session']}\n\n"
                         f"If you're sure you don't have an active session, use /reset to clear any stuck sessions."
                )
                return
            
            # Get exam_manager from context
            exam_manager = context.bot_data.get("exam_manager")
            if not exam_manager:
                error_msg = "exam_manager not found in context.bot_data!"
                logger.error(error_msg)
                await query.edit_message_text(f"❗ Internal error: {error_msg} Please use /reset and try again.")
                return
            
            # Start first exam
            logger.info(f"Calling exam_manager.start_first_exam for user {user_id}")
            result = exam_manager.start_first_exam(user_id)
            logger.info(f"start_first_exam result: {result}")
            
            if "error" in result:
                logger.error(f"Error starting first exam: {result['error']}")
                await query.edit_message_text(
                    f"❗ {result['error']}\n\n"
                    f"If you're having issues, try using /reset to clear any stuck sessions."
                )
                return
                
            # Check if first_question exists in result
            if "first_question" not in result:
                error_msg = "first_question not found in start_first_exam result!"
                logger.error(error_msg)
                await query.edit_message_text(
                    f"❗ Internal error: {error_msg}\n\n"
                    f"Please use /reset and try again."
                )
                return
                
            question = result["first_question"]
            logger.info(f"First question retrieved: {question.get('question', 'No question text')[:30]}...")
            
            # Instead of deleting the message, answer the callback and send a new message
            await query.answer("Starting First Exam")
            
            # Notify user that exam is starting
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["first_exam_start"]
            )
            
            # Send the first question
            await send_question(update, context, question)
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Error starting first exam: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await query.edit_message_text(
                f"❗ An error occurred when starting the exam: {str(e)}\n\n"
                f"Please use /reset and try again."
            )
        return
    
    # Process second exam options
    elif callback_data == "second_exam_options":
        # Create options keyboard for second exam
        keyboard = [
            [
                InlineKeyboardButton(texts["include_hashing"], callback_data="second_exam:include"),
                InlineKeyboardButton(texts["exclude_hashing"], callback_data="second_exam:exclude")
            ],
            [
                InlineKeyboardButton(texts["back_to_exam"], callback_data="back_to_mimic_command")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{texts['second_exam_header']}\n\n"
            f"{texts['second_exam_topics']}\n"
            f"{texts['second_exam_count']}\n\n"
            f"{texts['second_exam_option']}",
            reply_markup=reply_markup
        )
        return
        
    # Process second exam selection
    elif callback_data.startswith("second_exam:"):
        try:
            # Log action and available data
            logger.info(f"second_exam callback received from user {user_id}: {callback_data}")
            
            # Check if user has an active test session - with option to reset
            if has_active_test(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{texts['active_session']}\n\n"
                         f"If you're sure you don't have an active session, use /reset to clear any stuck sessions."
                )
                return
            
            # Get exam_manager from context
            exam_manager = context.bot_data.get("exam_manager")
            if not exam_manager:
                error_msg = "exam_manager not found in context.bot_data!"
                logger.error(error_msg)
                await query.edit_message_text(f"❗ Internal error: {error_msg} Please use /reset and try again.")
                return
            
            exclude_hashing = callback_data == "second_exam:exclude"
            logger.info(f"Starting second exam with exclude_hashing={exclude_hashing}")
            
            # Start second exam
            result = exam_manager.start_second_exam(user_id, exclude_hashing)
            logger.info(f"start_second_exam result: {result}")
            
            if "error" in result:
                logger.error(f"Error starting second exam: {result['error']}")
                await query.edit_message_text(
                    f"❗ {result['error']}\n\n"
                    f"If you're having issues, try using /reset to clear any stuck sessions."
                )
                return
                
            if "first_question" not in result:
                error_msg = "first_question not found in start_second_exam result!"
                logger.error(error_msg)
                await query.edit_message_text(
                    f"❗ Internal error: {error_msg}\n\n"
                    f"Please use /reset and try again."
                )
                return
                
            question = result["first_question"]
            logger.info(f"First question retrieved: {question.get('question', 'No question text')[:30]}...")
            
            # Answer the callback without deleting the message
            await query.answer("Starting Second Exam")
            
            # Notify user that exam is starting
            with_hashing_text = texts["with_hashing"] if not exclude_hashing else ""
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["second_exam_start"].format(with_hashing_text)
            )
            
            # Send the question as a new message
            await send_question(update, context, question)
        except Exception as e:
            logger.error(f"Error starting second exam: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await query.edit_message_text(
                f"❗ An error occurred when starting the exam: {str(e)}\n\n"
                f"Please use /reset and try again."
            )
        return
            
    # Process final exam options
    elif callback_data == "final_exam_options":
        # Create options keyboard for final exam
        keyboard = [
            [
                InlineKeyboardButton(texts["include_big_o"], callback_data="final_exam:include"),
                InlineKeyboardButton(texts["exclude_big_o"], callback_data="final_exam:exclude")
            ],
            [
                InlineKeyboardButton(texts["back_to_exam"], callback_data="back_to_mimic_command")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{texts['final_exam_header']}\n\n"
            f"{texts['final_exam_topics']}\n"
            f"{texts['final_exam_count']}\n\n"
            f"{texts['final_exam_option']}",
            reply_markup=reply_markup
        )
        return
        
    # Process final exam selection
    elif callback_data.startswith("final_exam:"):
        try:
            # Log action and available data
            logger.info(f"final_exam callback received from user {user_id}: {callback_data}")
            
            # Check if user has an active test session - with option to reset
            if has_active_test(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{texts['active_session']}\n\n"
                         f"If you're sure you don't have an active session, use /reset to clear any stuck sessions."
                )
                return
            
            # Get exam_manager from context
            exam_manager = context.bot_data.get("exam_manager")
            if not exam_manager:
                error_msg = "exam_manager not found in context.bot_data!"
                logger.error(error_msg)
                await query.edit_message_text(f"❗ Internal error: {error_msg} Please use /reset and try again.")
                return
            
            exclude_big_o = callback_data == "final_exam:exclude"
            logger.info(f"Starting final exam with exclude_big_o={exclude_big_o}")
            
            # Start final exam
            result = exam_manager.start_final_exam(user_id, exclude_big_o)
            logger.info(f"start_final_exam result: {result}")
            
            if "error" in result:
                logger.error(f"Error starting final exam: {result['error']}")
                await query.edit_message_text(
                    f"❗ {result['error']}\n\n"
                    f"If you're having issues, try using /reset to clear any stuck sessions."
                )
                return
                
            if "first_question" not in result:
                error_msg = "first_question not found in start_final_exam result!"
                logger.error(error_msg)
                await query.edit_message_text(
                    f"❗ Internal error: {error_msg}\n\n"
                    f"Please use /reset and try again."
                )
                return
                
            question = result["first_question"]
            logger.info(f"First question retrieved: {question.get('question', 'No question text')[:30]}...")
            
            # Answer the callback without deleting the message
            await query.answer("Starting Final Exam")
            
            # Notify user that exam is starting
            without_big_o_text = texts["without_big_o"] if exclude_big_o else ""
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["final_exam_start"].format(without_big_o_text)
            )
            
            # Send the question as a new message
            await send_question(update, context, question)
        except Exception as e:
            logger.error(f"Error starting final exam: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await query.edit_message_text(
                f"❗ An error occurred when starting the exam: {str(e)}\n\n"
                f"Please use /reset and try again."
            )
        return
        
    elif callback_data == "back_to_mimic_command":
        # Return to exam selection menu
        keyboard = [
            [InlineKeyboardButton(texts["first_exam_desc"], callback_data="start_first_exam")],
            [InlineKeyboardButton(texts["second_exam_desc"], callback_data="second_exam_options")],
            [InlineKeyboardButton(texts["final_exam_desc"], callback_data="final_exam_options")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{texts['mimic_exam_header']}\n\n"
            f"{texts['mimic_exam_intro']}\n\n"
            f"{texts['first_exam_desc']}\n"
            f"{texts['second_exam_desc']}\n"
            f"{texts['final_exam_desc']}\n\n"
            f"{texts['exam_experience_note']}",
            reply_markup=reply_markup
        )
        return
    
    # Handle showing detailed results
    elif callback_data == "show_detailed_results":
        await handle_detailed_results_request(update, context, show_only_incorrect=False)
        return
        
    # Handle showing only incorrect answers
    elif callback_data == "show_incorrect_only":
        await handle_detailed_results_request(update, context, show_only_incorrect=True)
        return
        
    # Handle skipping exam details
    elif callback_data == "skip_exam_details":
        await query.edit_message_text(texts["skip_exam_details"])
        return
    
    # View results button handler
    elif callback_data == "view_results_command":
        try:
            # Call the button handler for results
            await handle_results_button(update, context)
        except Exception as e:
            logger.error(f"Error showing results: {str(e)}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error showing results: {str(e)}"
            )
        return
    
    # Process regular exam answer - MIMIC EXAM SHOULD NOT SHOW FEEDBACK AFTER EACH QUESTION
    elif callback_data.startswith("answer:"):
        try:
            # Log action
            logger.info(f"answer callback received from user {user_id}: {callback_data}")
            
            # Get exam_manager from context
            exam_manager = context.bot_data.get("exam_manager")
            if not exam_manager:
                error_msg = "exam_manager not found in context.bot_data!"
                logger.error(error_msg)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❗ Internal error: {error_msg} Please use /reset and try again."
                )
                return
            
            answer = callback_data.split(":")[-1]
            logger.info(f"Processing answer '{answer}' for user {user_id}")
            
            # Process the answer
            result = exam_manager.process_answer(user_id, answer)
            logger.info(f"process_answer result: {result}")
            
            if "error" in result:
                logger.error(f"Error processing answer: {result['error']}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❗ {result['error']}"
                )
                return
            
            # Edit the original message to disable buttons but keep the question content
            question = result.get("question", {})
            question_text = question.get("question", "")
            choices = question.get("choices", {})
            
            # Recreate the question message without buttons
            message_text = f"{question_text}\n\n"
            for option, text in choices.items():
                message_text += f"{option}. {text}\n"
            message_text += f"\n✅ Your answer: {answer}"
            
            # Edit the message without buttons
            await query.edit_message_text(
                text=message_text,
                reply_markup=None  # Remove the reply markup entirely
            )
            
            # Answer the callback
            await query.answer(f"Answer {answer} recorded")
            
            # If test completed, show results
            if result.get("test_completed", False):
                logger.info("Test completed, showing results")
                test_results = result["test_results"]
                
                # Log test results for debugging
                logger.info(f"Test results: {test_results}")
                
                # Show compact summary first
                await show_exam_completion(update, context, user_id, test_results)
            else:
                # Send next question
                next_question = result.get("next_question")
                if next_question:
                    logger.info(f"Sending next question: {next_question.get('question', 'No question text')[:30]}...")
                    await send_question(update, context, next_question)
                else:
                    logger.error("No next_question found in non-completed test result")
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❗ Error: Could not load the next question. Please use /reset and try again."
                    )
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Error processing exam answer: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❗ An error occurred when processing your answer: {str(e)}"
            )
        return
    
    # Process adaptive test answer - ADAPTIVE TEST SHOULD SHOW FEEDBACK AFTER EACH QUESTION
    elif callback_data.startswith("adaptive_answer:"):
        try:
            answer = callback_data.replace("adaptive_answer:", "")
            logger.info(f"Processing adaptive answer: {answer} for user {user_id}")
            
            # Process answer
            result = process_adaptive_answer(user_id, answer, all_mcqs)
            
            if "error" in result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ {result['error']}"
                )
                return
            
            # Edit the original message to disable buttons but keep the question content
            question = result.get("question", {})
            question_text = question.get("question", "")
            choices = question.get("choices", {})
            
            # Recreate the question message without buttons
            message_text = f"{question_text}\n\n"
            for option, text in choices.items():
                message_text += f"{option}. {text}\n"
            message_text += f"\n✅ Your answer: {answer}"
            
            # Edit the message without buttons
            await query.edit_message_text(
                text=message_text,
                reply_markup=None  # Remove the reply markup entirely
            )
            
            # Answer the callback without modifying the message
            await query.answer(f"Answer {answer} recorded")
            
            # Show answer result in user's language - ADAPTIVE TEST SHOULD SHOW FEEDBACK AFTER EACH QUESTION
            if result["correct"]:
                feedback_message = texts["correct"]
            else:
                feedback_message = texts["incorrect"].format(
                    result['correct_answer'],
                    result.get('explanation', texts.get('no_explanation', 'No explanation available.'))
                )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=feedback_message
            )
                
            # Handle next action
            next_action = result.get("next_action", {})
            action_type = next_action.get("type", "")
            
            # Special handling for mark weak and continue
            if action_type == "mark_weak_and_continue":
                # Show the warning message in user's language
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=next_action.get("message", texts["topic_weak"])
                )
                
                # Move to next topic
                next_topic = move_to_next_adaptive_topic(user_id)
                
                if next_topic:
                    # Start with a medium question for the next topic
                    next_question = get_random_question_by_topic_and_difficulty(next_topic, "Medium", all_mcqs)
                    
                    if next_question:
                        set_current_adaptive_question(user_id, next_question)
                        
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=texts["moving_next"].format(next_topic)
                        )
                        
                        await send_question(update, context, next_question)
                    else:
                        # No question available for this topic
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=texts["no_topic_questions"].format(next_topic)
                        )
                        
                        # Complete test
                        update_adaptive_test_results(user_id, "complete")
                        await show_adaptive_test_completion(update, context, user_id)
                else:
                    # No more topics, test complete
                    update_adaptive_test_results(user_id, "complete")
                    await show_adaptive_test_completion(update, context, user_id)
                
                return  # Exit handler since we've processed this case
            
            # Handle topic completion
            elif action_type == "topic_complete":
                # Show topic complete message in user's language
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=next_action.get("message", "Topic completed successfully!")
                )
                
                # Move to next topic
                next_topic = move_to_next_adaptive_topic(user_id)
                
                if next_topic:
                    # Start with a medium question for the next topic
                    next_question = get_random_question_by_topic_and_difficulty(next_topic, "Medium", all_mcqs)
                    
                    if next_question:
                        set_current_adaptive_question(user_id, next_question)
                        
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=texts["moving_next"].format(next_topic)
                        )
                        
                        await send_question(update, context, next_question)
                    else:
                        # No question available for this topic
                        update_adaptive_test_results(user_id, "complete")
                        await show_adaptive_test_completion(update, context, user_id)
                else:
                    # No more topics, test complete
                    update_adaptive_test_results(user_id, "complete")
                    await show_adaptive_test_completion(update, context, user_id)
                    
            # Handle topic max reached
            elif action_type == "topic_max_reached":
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=next_action.get("message", texts["max_reached"])
                )
                
                # Move to next topic
                next_topic = move_to_next_adaptive_topic(user_id)
                
                if next_topic:
                    next_question = get_unused_question_by_topic_and_difficulty(user_id, next_topic, "Medium", all_mcqs)
                    
                    if next_question:
                        set_current_adaptive_question(user_id, next_question)
                        await send_question(update, context, next_question)
                    else:
                        update_adaptive_test_results(user_id, "complete")
                        await show_adaptive_test_completion(update, context, user_id)
                else:
                    update_adaptive_test_results(user_id, "complete")
                    await show_adaptive_test_completion(update, context, user_id)
                    
            # Handle needs training completion
            elif action_type == "needs_training_complete":
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=next_action.get("message", "Moving to next topic")
                )
                
                # Move to next topic
                next_topic = move_to_next_adaptive_topic(user_id)
                
                if next_topic:
                    next_question = get_unused_question_by_topic_and_difficulty(user_id, next_topic, "Medium", all_mcqs)
                    if next_question:
                        set_current_adaptive_question(user_id, next_question)
                        await send_question(update, context, next_question)
                    else:
                        update_adaptive_test_results(user_id, "complete")
                        await show_adaptive_test_completion(update, context, user_id)
                else:
                    update_adaptive_test_results(user_id, "complete")
                    await show_adaptive_test_completion(update, context, user_id)
                    
            # Handle test completion
            elif action_type == "complete":
                # Test complete - don't send additional messages, just complete
                update_adaptive_test_results(user_id, "complete")
                await show_adaptive_test_completion(update, context, user_id)
                
            else:
                # CRITICAL FIX: Only show next_question messages, skip warning messages
                if (next_action.get("message") and 
                    action_type == "next_question"):
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=next_action.get("message")
                    )
                
                # Continue with next question if available
                if "next_question" in result:
                    await send_question(update, context, result["next_question"])
                else:
                    # No more questions, end test
                    update_adaptive_test_results(user_id, "complete")
                    await show_adaptive_test_completion(update, context, user_id)
                    
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Error in adaptive_answer: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Notify the user
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ An error occurred: {str(e)}. Please try again or use /reset."
            )
        return
    
    # Handle reevaluation answers - REEVALUATION SHOULD SHOW FEEDBACK AFTER EACH QUESTION
    elif callback_data.startswith("reevaluation_answer:"):
        try:
            # SIMPLE parsing - remove all session ID complexity
            parts = callback_data.replace("reevaluation_answer:", "").split(":")
            answer = parts[-1]  # Get the last part which should be the answer
            
            logger.info(f"Processing reevaluation answer: {answer} for user {user_id}")
            
            # CRITICAL FIX: Check session from database, not stale cache
            session = db_manager.load_user_session(user_id)
            
            # FIXED SESSION VALIDATION - Only check if session exists and is reevaluation
            if not session:
                await query.answer("No active test session. Please start a new test.")
                return
                
            # Verify this is actually a reevaluation session
            test_type = session.get("test_type", "")
            if not ("Reevaluation" in test_type):
                await query.answer("This is not a reevaluation test session.")
                return
                
            # Simple validation - just check if we have questions and valid index
            questions = session.get("questions", [])
            current_index = session.get("current_question_index", 0)
            if current_index >= len(questions):
                await query.answer("This test has already been completed.")
                return
            
            # FIXED: Use the correct function based on test type
            if "Advanced Reevaluation" in test_type:
                # Use advanced function for advanced reevaluation - SEQUENTIAL HARD QUESTIONS
                result = process_reevaluation_answer_advanced(user_id, answer)
            else:
                # Use normal function for normal reevaluation - SEQUENTIAL EASY/MEDIUM/HARD
                result = process_reevaluation_answer(user_id, answer)
            
            # Handle error case
            if "error" in result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ {result['error']}"
                )
                return
            
            # Edit the original message to disable buttons but keep the question content
            question = result.get("question", {})
            question_text = question.get("question", "")
            choices = question.get("choices", {})
            
            # Recreate the question message without buttons
            message_text = f"{question_text}\n\n"
            for option, text in choices.items():
                message_text += f"{option}. {text}\n"
            message_text += f"\n✅ Your answer: {answer}"
            
            # Edit the message without buttons
            await query.edit_message_text(
                text=message_text,
                reply_markup=None  # Remove the reply markup entirely
            )
            
            # Answer the callback
            await query.answer(f"Answer {answer} recorded")
            
            # Show answer result in user's language 
            if result["correct"]:
                feedback_message = texts["correct"]
            else:
                # Use a fallback if explanation is missing or texts["incorrect"] is missing
                explanation = result.get('explanation', 'No explanation available.')
                
                if "incorrect" in texts:
                    feedback_message = texts["incorrect"].format(
                        result['correct_answer'],
                        explanation
                    )
                else:
                    # Fallback format if translation is missing
                    feedback_message = (
                        f"❌ Incorrect!\n\n"
                        f"The correct answer is: {result['correct_answer']}\n\n"
                        f"📚 Explanation:\n{explanation}"
                    )
            
            # Send feedback for the answer
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=feedback_message
            )
                
            if result.get("test_completed", False):
                # Show test completion message
                test_results = result.get("test_results", {})
                
                # Format completion message based on number of topics
                topics = test_results.get("topics", [])
                topic_text = f"Topic: {topics[0]}" if len(topics) == 1 else f"Topics: {', '.join(topics)}"
                
                if "reevaluation_completed" in texts:
                    completion_message = texts["reevaluation_completed"].format(
                        topic_text,
                        test_results.get('score', 'N/A')
                    )
                else:
                    # Fallback if translation is missing
                    completion_message = (
                        f"🎓 Reevaluation Test Completed!\n\n"
                        f"{topic_text}\n"
                        f"Score: {test_results.get('score', 'N/A')}\n\n"
                    )
                
                # Show status of each topic
                weak_topics = test_results.get("weak_topics", [])
                for topic in topics:
                    if topic in weak_topics:
                        if "topic_still_weak" in texts:
                            completion_message += texts["topic_still_weak"].format(topic)
                        else:
                            completion_message += f"⚠️ {topic}: Still weak, needs more review.\n"
                    else:
                        if "topic_improved" in texts:
                            completion_message += texts["topic_improved"].format(topic)
                        else:
                            completion_message += f"✅ {topic}: Improved! Good job.\n"
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=completion_message
                )
                
                # Show navigation options with localized buttons
                await show_navigation_options(update, context, user_id)
                
            else:
                # Continue with the next question
                if "next_question" in result:
                    try:
                        logger.info(f"Sending next reevaluation question for user {user_id}")
                        await send_question(update, context, result["next_question"])
                    except Exception as e:
                        logger.error(f"Error sending next question: {str(e)}")
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"Error sending next question: {str(e)}. Please use /reset and try again."
                        )
                else:
                    logger.error(f"No next_question found in reevaluation result for user {user_id}")
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Error: Could not load the next question. Please use /reset and try again."
                    )
        except Exception as e:
            logger.error(f"Error processing reevaluation answer: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ An error occurred while processing your answer: {str(e)}. Please use /reset and try again."
            )
        return
    
    # Topic selection for adaptive test
    elif callback_data.startswith("select_topic:"):
        if user_id not in user_selections:
            await query.edit_message_text(texts["session_expired"])
            return
            
        topic = callback_data.replace("select_topic:", "")
        
        # Toggle selection
        if topic in user_selections[user_id]["selected_topics"]:
            user_selections[user_id]["selected_topics"].remove(topic)
        else:
            user_selections[user_id]["selected_topics"].append(topic)
        
        # Recreate keyboard with updated selection
        keyboard = []
        for t in user_selections[user_id]["all_topics"]:
            prefix = "☑" if t in user_selections[user_id]["selected_topics"] else "☐"
            keyboard.append([
                InlineKeyboardButton(f"{prefix} {t}", callback_data=f"select_topic:{t}")
            ])
        
        # Add control buttons with translated text
        keyboard.append([
            InlineKeyboardButton(texts["select_all"], callback_data="select_all"),
            InlineKeyboardButton(texts["clear_all"], callback_data="clear_all")
        ])
        keyboard.append([
            InlineKeyboardButton(texts["start_test"], callback_data="start_test")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            texts["welcome_adaptive"],
            reply_markup=reply_markup
        )
        return
    
    # Select all topics
    elif callback_data == "select_all":
        if user_id not in user_selections:
            await query.edit_message_text(texts["session_expired"])
            return
            
        user_selections[user_id]["selected_topics"] = user_selections[user_id]["all_topics"].copy()
        
        # Recreate keyboard with all selected
        keyboard = []
        for topic in user_selections[user_id]["all_topics"]:
            keyboard.append([
                InlineKeyboardButton(f"☑ {topic}", callback_data=f"select_topic:{topic}")
            ])
        
        # Add control buttons with translated text
        keyboard.append([
            InlineKeyboardButton(texts["select_all"], callback_data="select_all"),
            InlineKeyboardButton(texts["clear_all"], callback_data="clear_all")
        ])
        keyboard.append([
            InlineKeyboardButton(texts["start_test"], callback_data="start_test")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            texts["welcome_adaptive"],
            reply_markup=reply_markup
        )
        return
    
    # Clear all topics
    elif callback_data == "clear_all":
        if user_id not in user_selections:
            await query.edit_message_text(texts["session_expired"])
            return
            
        user_selections[user_id]["selected_topics"] = []
        
        # Recreate keyboard with none selected
        keyboard = []
        for topic in user_selections[user_id]["all_topics"]:
            keyboard.append([
                InlineKeyboardButton(f"☐ {topic}", callback_data=f"select_topic:{topic}")
            ])
        
        # Add control buttons with translated text
        keyboard.append([
            InlineKeyboardButton(texts["select_all"], callback_data="select_all"),
            InlineKeyboardButton(texts["clear_all"], callback_data="clear_all")
        ])
        keyboard.append([
            InlineKeyboardButton(texts["start_test"], callback_data="start_test")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            texts["welcome_adaptive"],
            reply_markup=reply_markup
        )
        return
    
    # Start adaptive test
    elif callback_data == "start_test":
        if user_id not in user_selections:
            await query.edit_message_text(texts["session_expired"])
            return
            
        selected_topics = user_selections[user_id]["selected_topics"]
        
        if not selected_topics:
            await query.edit_message_text(texts["please_select"])
            return
        
        # Start adaptive test session
        start_adaptive_test_session(user_id, selected_topics)
        
        # Get first topic and medium question
        first_topic = get_current_adaptive_topic(user_id)
        
        if not first_topic:
            await query.edit_message_text(texts["error_starting"])
            return
            
        first_question = get_random_question_by_topic_and_difficulty(first_topic, "Medium", all_mcqs)
        
        if not first_question:
            await query.edit_message_text(
                texts["no_questions"].format(first_topic)
            )
            return
            
        # Set current question
        set_current_adaptive_question(user_id, first_question)
        
        # Inform user test has started
        await query.edit_message_text(
            texts["test_started"].format(first_topic)
        )
        
        # Send first question
        await send_question(update, context, first_question)
        return
    
    # Start regular reevaluation test
    elif callback_data.startswith("start_reevaluation:"):
        try:
            topic = callback_data.replace("start_reevaluation:", "")
            logger.info(f"Starting reevaluation for topic {topic} for user {user_id}")
            
            # FORCE CLEAR ANY EXISTING SESSION - no more warnings, just clear
            user_info = get_user_data(user_id)
            
            # Immediately clear both database and memory
            db_manager.clear_user_session(user_id)
            user_info["current_test_session"] = None
            save_user_data()
            
            logger.info(f"Cleared any existing session for user {user_id} before starting reevaluation")
            
            # Send a new message to show we're starting
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["starting_reevaluation"].format(topic)
            )
            
            # Start reevaluation test
            result = start_reevaluation_test(user_id, topic, all_mcqs)
            
            if "error" in result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ {result['error']}"
                )
                return
            
            # Show reevaluation test intro with a very clear indicator
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["new_reevaluation"].format(topic)
            )
            
            # Send first question
            if "first_question" in result:
                await send_question(update, context, result["first_question"])
            else:
                logger.error(f"No first_question in reevaluation result: {result}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Error: Could not start reevaluation test. Please use /reset and try again."
                )
        except Exception as e:
            logger.error(f"Error starting reevaluation for user {user_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texts["reevaluation_error"]
            )
        return

    # Start advanced reevaluation test
    elif callback_data.startswith("start_advanced_reevaluation:"):
        await handle_advanced_reevaluation_callback(update, context, callback_data)
        return
    
    # Skip reevaluation
    elif callback_data == "skip_reevaluation":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=texts["reevaluation_skipped"]
        )
        return
        
    # Continue adaptive test after declining reevaluation
    elif callback_data == "continue_adaptive_test":
        # Move to the next topic
        next_topic = move_to_next_adaptive_topic(user_id)
        
        if next_topic:
            # Get a medium question for the next topic
            next_question = get_random_question_by_topic_and_difficulty(next_topic, "Medium", all_mcqs)
            
            if next_question:
                set_current_adaptive_question(user_id, next_question)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=texts["returning_adaptive"].format(next_topic)
                )
                
                await send_question(update, context, next_question)
            else:
                # No question available for this topic
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=texts["no_topic_questions"].format(next_topic)
                )
                
                # Complete test
                update_adaptive_test_results(user_id, "complete")
                
                # Show test completion message
                await show_adaptive_test_completion(update, context, user_id)
        else:
            # No more topics, test complete
            update_adaptive_test_results(user_id, "complete")
            
            # Show test completion message
            await show_adaptive_test_completion(update, context, user_id)
        return
    
    # Handle reevaluation options
    elif callback_data.startswith("reevaluation:"):
        parts = callback_data.split(":")
        choice = parts[1] if len(parts) > 1 else ""
        topic = parts[2] if len(parts) > 2 else ""
        
        if choice == "yes" and topic:
            # Start reevaluation test
            result = start_reevaluation_test(user_id, topic, all_mcqs)
            
            if "error" in result:
                await query.edit_message_text(f"❗ {result['error']}")
                return
                
            question = result["first_question"]
            
            # Send the question as a new message
            await query.delete_message()
            await send_question(update, context, question)
        else:
            # User declined reevaluation
            await query.edit_message_text(
                texts["reevaluation_skipped"]
            )
            
            # Clear the current test session or continue with the next topic
            if is_adaptive_test(user_id):
                # Move to the next topic
                next_topic = move_to_next_adaptive_topic(user_id)
                
                if next_topic:
                    next_question = get_random_question_by_topic_and_difficulty(next_topic, "Medium", all_mcqs)
                    
                    if next_question:
                        set_current_adaptive_question(user_id, next_question)
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=texts["returning_adaptive"].format(next_topic)
                        )
                        await send_question(update, context, next_question)
                    else:
                        # No question available, end test
                        update_adaptive_test_results(user_id, "complete")
                        await show_adaptive_test_completion(update, context, user_id)
                else:
                    # No more topics, end test
                    update_adaptive_test_results(user_id, "complete")
                    await show_adaptive_test_completion(update, context, user_id)
            else:
                # If not in an adaptive test, just clear the session
                user_info = get_user_data(user_id)
                user_info["current_test_session"] = None
                save_user_data()
                
                # Show available commands
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You can now use /adaptive_test or /mimic_incamp_exam to start a new test."
                )
        return
    
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages."""
    text = update.message.text.strip()
    user_id = str(update.effective_user.id)
    
    # Get user's language preference
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Check if user is in an active test session
    if has_active_test(user_id):
        # Check if this is a valid answer format (A, B, C, D, E)
        if text.upper() in ["A", "B", "C", "D", "E"]:
            all_mcqs = context.bot_data.get("all_mcqs", [])
            
            if is_adaptive_test(user_id):
                # Process adaptive test answer
                result = process_adaptive_answer(user_id, text.upper(), all_mcqs)
            else:
                # Process reevaluation test answer
                result = process_reevaluation_answer(user_id, text.upper())
            
            if "error" in result:
                await update.message.reply_text(f"⚠️ {result['error']}")
                return
            
            # Handle answer result
            if result["correct"]:
                feedback = "✅ Correct!"
            else:
                feedback = (
                    f"❌ Incorrect!\n\n"
                    f"The correct answer is: {result['correct_answer']}\n\n"
                    f"📚 Explanation:\n{result['explanation']}"
                )
            
            await update.message.reply_text(feedback)
            
            # Handle next steps based on test type
            if is_adaptive_test(user_id):
                # Handle adaptive test next action
                next_action = result.get("next_action", {})
                action_type = next_action.get("type")
                
                if action_type == "offer_reevaluation":
                    # Offer reevaluation
                    keyboard = [
                        [
                            InlineKeyboardButton("Yes", callback_data=f"start_reevaluation:{next_action.get('topic')}"),
                            InlineKeyboardButton("No", callback_data="continue_adaptive_test")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        next_action.get("message", "Would you like to take a reevaluation test?"),
                        reply_markup=reply_markup
                    )
                elif action_type == "warning":
                    # Show warning and continue
                    await update.message.reply_text(next_action.get("message", ""))
                    
                    # Send next question
                    if "next_question" in result:
                        await send_question(update, context, result["next_question"])
                elif action_type in ["topic_complete", "complete"]:
                    # Show completion message
                    update_adaptive_test_results(user_id, "complete")
                    await show_adaptive_test_completion(update, context, user_id)
                else:
                    # Send next question if available
                    if "next_question" in result:
                        await send_question(update, context, result["next_question"])
            else:
                # Handle reevaluation test completion
                if result.get("test_completed", False):
                    test_results = result.get("test_results", {})
                    
                    completion_message = (
                        f"🎓 Reevaluation Test Completed!\n\n"
                        f"Topic: {test_results.get('test_type', '').replace('Reevaluation: ', '')}\n"
                        f"Score: {test_results.get('score', 'N/A')}\n\n"
                    )
                    
                    if test_results.get("weak_topics", []):
                        completion_message += (
                            f"⚠️ This topic is still marked as weak. "
                            f"Consider reviewing it more thoroughly."
                        )
                    else:
                        completion_message += (
                            f"✅ Good job! You've shown improvement on this topic."
                        )
                    
                    await update.message.reply_text(completion_message)
                else:
                    # Send next question
                    if "next_question" in result:
                        await send_question(update, context, result["next_question"])
        else:
            await update.message.reply_text(
                "🔤 Please answer with A, B, C, D, or E only."
            )
    else:
        user = update.effective_user
        bot_desc = texts['bot_description']
        if "Here's how to use me:" in bot_desc:
            bot_desc = bot_desc.split("Here's how to use me:")[0].strip()
        elif "إليك كيفية استخدامي:" in bot_desc:
            bot_desc = bot_desc.split("إليك كيفية استخدامي:")[0].strip()
        
        welcome_message = (
            f"👋 {texts['hello']} {user.first_name}! {texts['welcome_to_bot']}\n\n"
            f"{texts['use_start_command']}\n\n"  
        )
        
        await update.message.reply_text(welcome_message)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram-bot-api."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Send error message to user if possible
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❗ An error occurred while processing your request. Please try again."
        )
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset user's active test session with comprehensive cleanup."""
    user_id = str(update.effective_user.id)
    logger.info(f"Reset command called by user {user_id}")
    
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    try:
        # COMPLETELY reset all user session data
        if user_id in user_data:
            # Log what was active for debugging
            session_type = "None"
            if user_data[user_id].get("current_test_session"):
                session_type = user_data[user_id].get("current_test_session", {}).get("test_type", "Unknown")
            logger.info(f"Resetting session type: {session_type}")
            
            # Clear current test session and any backups or references
            user_data[user_id]["current_test_session"] = None
            
            # Clear session backup if it exists
            if "session_backup" in user_data[user_id]:
                del user_data[user_id]["session_backup"]
            
            # Clear any ignore timestamps
            if "ignore_before_time" in user_data[user_id]:
                user_data[user_id]["ignore_before_time"] = {}
                
            # Clear last exam results if they exist
            if "last_exam_results" in user_data[user_id]:
                del user_data[user_id]["last_exam_results"]
        
        # Clear any selections data
        if user_id in user_selections:
            del user_selections[user_id]
        
        # Save changes
        save_user_data()
        
        # Force refresh user data in memory
        if user_id in user_data:
            user_data[user_id] = {
                "tests": user_data[user_id].get("tests", []),
                "adaptive_tests": user_data[user_id].get("adaptive_tests", []),
                "weak_topic_pool": user_data[user_id].get("weak_topic_pool", []),
                "current_test_session": None
            }
        
        # Provide clear confirmation in user's language
        await update.message.reply_text(texts["reset_confirmation"])
        
        # Show navigation options with localized buttons
        await show_navigation_options(update, context, user_id)
        
        logger.info(f"Reset completed successfully for user {user_id}")
    except Exception as e:
        # If regular reset fails, try emergency cleanup
        logger.error(f"Error during reset: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            # Direct cleanup of user data
            if user_id in user_data:
                # Complete fresh reset of the user data
                user_data[user_id] = {
                    "tests": user_data[user_id].get("tests", []),
                    "adaptive_tests": user_data[user_id].get("adaptive_tests", []),
                    "weak_topic_pool": user_data[user_id].get("weak_topic_pool", []),
                    "current_test_session": None
                }
                save_user_data()
                
            if user_id in user_selections:
                del user_selections[user_id]
                
            await update.message.reply_text(
                "✅ Reset completed with recovery procedure.\n\n"
                "You can now use /adaptive_test or other commands."
            )
            
            # Show navigation options even after emergency recovery
            await show_navigation_options(update, context, user_id)
            
            logger.info(f"Reset completed with recovery procedure for user {user_id}")
        except Exception as recovery_error:
            # If all else fails, try system-level reset
            logger.error(f"Recovery procedure failed: {recovery_error}")
            
            # Force reset with lowest level direct data manipulation
            if user_id in user_data:
                try:
                    user_data[user_id] = {
                        "tests": user_data[user_id].get("tests", []),
                        "adaptive_tests": user_data[user_id].get("adaptive_tests", []),
                        "weak_topic_pool": user_data[user_id].get("weak_topic_pool", []),
                        "current_test_session": None
                    }
                    save_user_data()
                except:
                    # Last resort - completely reset the user's data
                    user_data[user_id] = {
                        "tests": [],
                        "adaptive_tests": [],
                        "weak_topic_pool": [],
                        "current_test_session": None
                    }
                    save_user_data()
            
            await update.message.reply_text(
                "✅ Emergency reset completed. Your session has been cleared.\n\n"
                "You can now use /adaptive_test or /mimic_incamp_exam to start a new test."
            )
            
            # Show navigation options even after emergency reset
            await show_navigation_options(update, context, user_id)
            
            logger.info(f"Emergency reset completed for user {user_id}")

async def mimic_incamp_exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /mimic_incamp_exam command with multilingual support."""
    user_id = str(update.effective_user.id)
    
    # Get user's language
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    # Add detailed logging
    logger.info(f"mimic_incamp_exam command called by user {user_id}")

    # Check for stale session and force reset
    if user_id in user_data:
        session = user_data[user_id].get("current_test_session")
        if session:
            # Check if session is stale or broken
            is_valid_session = True
            
            if "questions" in session and "current_question_index" in session:
                questions = session.get("questions", [])
                current_index = session.get("current_question_index", 0)
                
                if not questions or current_index >= len(questions):
                    is_valid_session = False
                    logger.warning(f"Found stale session for user {user_id}. Forcing reset.")
            
            # Detect other kinds of broken sessions
            if session.get("test_type") and not isinstance(session.get("test_type"), str):
                is_valid_session = False
            
            # Force reset stale or invalid sessions
            if not is_valid_session:
                user_data[user_id]["current_test_session"] = None
                save_user_data()
                logger.info(f"Cleared stale session for user {user_id}")
    
    # Double-check session 
    if has_active_test(user_id):
        # Modified message that includes reset command
        await update.message.reply_text(
            f"{texts['active_session']}\n\n"
            f"If you're sure you don't have an active session, use /reset to clear any stuck sessions."
        )
        return
    
    # Show subject selection first
    keyboard = [
        [InlineKeyboardButton("CS211 DATA STRUCTURE", callback_data="subject_mimic:CS211")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        texts["select_subject"],
        reply_markup=reply_markup
    )

async def first_exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /first_exam command."""
    user_id = str(update.effective_user.id)
    
    result = context.bot_data.get("exam_manager").start_first_exam(user_id)
    
    if "error" in result:
        await update.message.reply_text(f"❗ {result['error']}")
        return
        
    question = result["first_question"]
    
    # Format and send the question
    await send_question(update, context, question)

async def second_exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /second_exam command."""
    # Create keyboard for exclusion options
    keyboard = [
        [
            InlineKeyboardButton("Include Hashing", callback_data="second_exam:include"),
            InlineKeyboardButton("Exclude Hashing", callback_data="second_exam:exclude")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🧠 Second Exam: Stacks, Queues, Recursion, Hashing\n\n"
        "Would you like to include or exclude the Hashing topic?",
        reply_markup=reply_markup
    )

async def final_exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /final_exam command."""
    # Create keyboard for exclusion options
    keyboard = [
        [
            InlineKeyboardButton("Include Big-O", callback_data="final_exam:include"),
            InlineKeyboardButton("Exclude Big-O", callback_data="final_exam:exclude")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 Final Exam: All Topics\n\n"
        "Would you like to include or exclude the Big-O topic?",
        reply_markup=reply_markup
    )

def main() -> None:
    """Set up and run the bot."""
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run JUSTLearn Adaptive Test Bot')
    parser.add_argument('--token', type=str, required=True, help='Telegram bot token')
    parser.add_argument('--db-path', type=str, default='data/justlearn.db', help='Path to SQLite database')
    parser.add_argument('--reset-all', action='store_true', help='Reset all active sessions on startup')
    args = parser.parse_args()
    
    # Initialize database manager
    global db_manager
    db_manager = DatabaseManager(args.db_path)
    
    # Load MCQs from database
    all_mcqs = db_manager.load_mcqs()
    if not all_mcqs:
        logger.error(f"No MCQs loaded. Please check the database at {args.db_path}")
        return
    
    # Reset all active sessions if requested
    if args.reset_all:
        users_reset = 0
        # Get all users with active sessions and clear them
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM user_sessions')
            active_users = [row['user_id'] for row in cursor.fetchall()]
            
            for user_id in active_users:
                db_manager.clear_user_session(user_id)
                users_reset += 1
        
        if users_reset > 0:
            logger.info(f"Reset active sessions for {users_reset} users")
    
    # Create the Application with job_queue enabled 
    application = Application.builder().token(args.token).build()
    
    # Initialize components with database
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from bot.search_engine import SearchEngine
        from bot.user_tracker import UserTracker
        from bot.exam_manager import ExamManager
        
        # Create instances with database path
        search_engine_instance = SearchEngine(db_path=args.db_path)
        user_tracker_instance = UserTracker(db_path=args.db_path)
        exam_manager_instance = ExamManager(search_engine_instance, user_tracker_instance)
        
        logger.info("Successfully imported and initialized all components with database")
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        logger.error("Trying alternative import paths...")
        
        # Try alternate import paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        sys.path.extend([current_dir, parent_dir])
        
        from bot.search_engine import SearchEngine
        from bot.user_tracker import UserTracker
        from bot.exam_manager import ExamManager
        
        # Create instances with database path
        search_engine_instance = SearchEngine(db_path=args.db_path)
        user_tracker_instance = UserTracker(db_path=args.db_path)
        exam_manager_instance = ExamManager(search_engine_instance, user_tracker_instance)
        
        logger.info("Successfully imported and initialized components using alternative paths with database")
    
    # Store data in the application's bot_data
    application.bot_data["all_mcqs"] = all_mcqs
    application.bot_data["exam_manager"] = exam_manager_instance
    application.bot_data["search_engine"] = search_engine_instance
    application.bot_data["user_tracker"] = user_tracker_instance
    application.bot_data["db_manager"] = db_manager  # Add database manager to bot_data
    
    logger.info("Initialized and stored components in application.bot_data with database")
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("subjects", subjects_command))
    application.add_handler(CommandHandler("topics", topics_command))
    application.add_handler(CommandHandler("adaptive_test", adaptive_test_command))
    application.add_handler(CommandHandler("results", results_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("contact_us", contact_us_command))

    # Add mimic_incamp_exam related handlers
    application.add_handler(CommandHandler("mimic_incamp_exam", mimic_incamp_exam_command))
    application.add_handler(CommandHandler("first_exam", first_exam_command))
    application.add_handler(CommandHandler("second_exam", second_exam_command))
    application.add_handler(CommandHandler("final_exam", final_exam_command))
    
    # Add reminder command handler
    application.add_handler(CommandHandler("set_reminder", set_reminder_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Restore reminder jobs for users who had them enabled (now from database)
    restore_reminder_jobs_from_db(application)
    
    # Run the bot
    logger.info("Starting the JUSTLearn Adaptive Test Bot with SQLite database...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()