"""bits: functions on bit strings with a fixed dimension."""

import re
BIT_STRING_PATTERN = re.compile("[01]+")
WILDCARD_STRING_PATTERN = re.compile("[01*]+")

def bit_string_to_int(bits: str) -> int:
    """Convert the given bit string to an int."""
    if not BIT_STRING_PATTERN.fullmatch(bits):
        raise ValueError("Badly formed bit string")
    result = 0
    for bit in bits:
        result = result << 1
        result += int(bit)
    return result

def int_to_bit_string(number : int, dimension : int) -> str:
    """Convert `number` to a bit string of the given `dimension`."""
    if number < 0 or number >= 2 ** dimension:
        raise ValueError(f"Given {number}, but the number "
                         + "must be in the range [0,2**dimension).")
    if dimension < 0:
        raise ValueError(f"Given {dimension}, but the dimension "
                         + "must be nonnegative.")
    if dimension == 0:
        return "0"
    format_string = "{:0" + str(dimension) + "b}"
    return format_string.format(number)

def weight(number : int) -> int:
    """Return how many `1`s in the binary representation of `number`."""
    if number < 0:
        raise ValueError(f"Given {number}, but the number must be nonnegative.")
    number_of_bits = 0
    while number > 0:
        number_of_bits += number % 2
        number = number >> 1
    return number_of_bits

def permute_bits_by_index_list(number: int,
                               list_of_indices: list,
                               dimension: int) -> int:
    """Permute `number`'s binary representation by the list of indices."""
    if dimension < 0:
        raise ValueError(f"Given {dimension}, but the "
                         + "dimension must be nonnegative.")
    if len(list_of_indices) != dimension:
        raise ValueError(f"Given a list of length {len(list_of_indices)}, "
                         + "but the list of indices must be "
                         + f"of length {dimension}.\n"
                         + f"List: {list_of_indices}")
    if not all([i in list_of_indices for i in range(dimension)]):
        raise ValueError("The list does not specify a valid permutation.")

    bit_string = int_to_bit_string(number, dimension)
    value = ""
    # pylint: disable=pointless-statement
    # This is accumulation via list comprehension:
    [ value := value + bit_string[i] for i in list_of_indices]
    return bit_string_to_int(value)

def truncate_within_dimension(number: int, dimension: int) -> int:
    """Truncate `number` within `dimension` bits."""
    all_ones_mask = (2 ** dimension) - 1
    return number & all_ones_mask

def pattern_to_int_list(pattern : str,
                        dimension : int) -> list:
    """Turn a subcube string into a list of integers
    whose binary representation matches the string.

    The string is made up of `1`, `0`, and `*`:
    - `1` matches `1`.
    - `0` matches `0`.
    - `*` matches `1` or `0`.

    """
    if not WILDCARD_STRING_PATTERN.fullmatch(pattern):
        raise ValueError(f"Given {pattern}, but the string "
                         + "needs to consist of 1, 0, and *.")
    if len(pattern) != dimension:
        raise ValueError(f"Given {pattern}, but the string "
                         + f"needs to be of length {dimension}.")

    def matches(number : int) -> bool:
        number_as_string = int_to_bit_string(number, dimension)
        for i in range(dimension):
            if pattern[i] == "*":
                continue
            if pattern[i] != number_as_string[i]:
                return False
        return True

    number_of_bit_strings = 2 ** dimension
    ints_that_match = list(filter(matches, range(number_of_bit_strings)))
    return ints_that_match

def strings_to_int_list(bit_strings : list, dimension : int):
    """Turn the given list of bit strings into a list of integers,
    but only if they actually match `dimension`.

    """
    if not all((len(string) == dimension) for string in bit_strings):
        raise ValueError(f"All bit strings must be of length {dimension}.")
    return list(map(bit_string_to_int, bit_strings))

def how_many_bit_strings(dimension : int) -> int:
    """Return the number of possible bit strings of
    length `dimension`.

    """
    if dimension < 0: return 0
    return 2 ** dimension

def reverse(number : int, dimension : int) -> int:
    """Given the number, return the number with bits reversed."""
    bit_string = int_to_bit_string(number, dimension)
    bit_string = bit_string[::-1] # reverses it
    return bit_string_to_int(bit_string)
