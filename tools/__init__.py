from tools.trivia_qa import answer_trivia
from tools.find_replace import find_replace
from tools.reminder import set_reminder, list_reminders
from tools.calendar import find_free_time
from tools.math_solver import solve_math
from tools.summarizer import summarize_article
from tools.unit_test_gen import generate_unit_tests
from tools.multi_tool_chain import multi_tool_chain

TOOL_REGISTRY = {
    "answer_trivia":      answer_trivia,
    "find_replace":       find_replace,
    "set_reminder":       set_reminder,
    "list_reminders":     list_reminders,
    "find_free_time":     find_free_time,
    "solve_math":         solve_math,
    "summarize_article":  summarize_article,
    "generate_unit_tests": generate_unit_tests,
    "multi_tool_chain":   multi_tool_chain,
}
