import pytest

from src.interpreter import MiniInterpreter


class TestClasses:
    interpreter = MiniInterpreter()

    def test_primary(self):
        code = """
        Person := class (name, age, gender) {
            year_of_birth := 2024 - age;
            change_name := function(this, new_name) this.name := new_name;
        }
        
        
        person_1 := Person("John", 24, "M")
        person_1.change_name("Bill")
        person_1.name
        
        """
        expected = "Bill"

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected

    # def test_factory(self):
    #     code = """
    #     Person := class (name, age, gender) {
    #         year_of_birth := 2024 - age;
    #         change_name := function(this, new_name) this.name := new_name;
    #     }
    #
    #     create_new_person := function(...args) Person(...args);
    #
    #
    #     person_1 := create_new_person("John", 24, "M")
    #     person_1.change_name("Bill")
    #     person_1.name
    #
    #     """
    #     expected = "Bill"
    #
    #     actual_value = self.interpreter.execute(code)
    #     assert actual_value == expected
