"""Reference extended Hamming (8,4) and Reed–Solomon (255,223) codecs."""
from dataclasses import dataclass
from functools import reduce
from operator import xor


class Uncorrectable(ValueError):
    """A received word cannot be safely corrected by this code."""


DATA_POSITIONS = (3, 5, 6, 7)
PARITY_POSITIONS = (1, 2, 4)


@dataclass(frozen=True)
class HammingResult:
    value: int
    codeword: tuple[int, ...]
    syndrome: int
    corrected_position: int | None


def hamming_encode(value):
    """Encode a four-bit integer into positions 1 through 8."""
    if type(value) is not int or not 0 <= value < 16:
        raise ValueError("Hamming input must be a four-bit integer")
    word = [0] * 8
    for shift, position in zip((3, 2, 1, 0), DATA_POSITIONS):
        word[position - 1] = (value >> shift) & 1
    for parity in PARITY_POSITIONS:
        word[parity - 1] = sum(word[i - 1] for i in range(1, 8) if i & parity) % 2
    word[7] = sum(word[:7]) % 2
    return tuple(word)


def hamming_decode(word):
    """Correct any single-bit flip or raise on a detected double-bit flip."""
    word = list(word)
    if len(word) != 8 or any(type(bit) is not int or bit not in (0, 1) for bit in word):
        raise ValueError("Hamming word must have eight binary digits")
    syndrome = reduce(xor, (i for i in range(1, 8) if word[i - 1]), 0)
    corrected = None
    if sum(word) % 2:
        corrected = syndrome or 8
        word[corrected - 1] ^= 1
    elif syndrome:
        raise Uncorrectable(f"Hamming detected an even error pattern, syndrome {syndrome}")
    value = 0
    for position in DATA_POSITIONS:
        value = (value << 1) | word[position - 1]
    return HammingResult(value, tuple(word), syndrome, corrected)


RS_TOTAL = 255
RS_DATA = 223
RS_PARITY = RS_TOTAL - RS_DATA
FIELD_POLYNOMIAL = 0x11D


def _field_tables():
    powers = []
    logs = [0] * 256
    value = 1
    for exponent in range(255):
        powers.append(value)
        logs[value] = exponent
        value <<= 1
        if value & 0x100:
            value ^= FIELD_POLYNOMIAL
    return tuple(powers + powers), tuple(logs)


POWERS, LOGS = _field_tables()


def _multiply(a, b):
    return POWERS[LOGS[a] + LOGS[b]] if a and b else 0


def _divide(a, b):
    if not b:
        raise ZeroDivisionError("cannot divide by zero in GF(256)")
    return POWERS[LOGS[a] - LOGS[b] + 255] if a else 0


def _evaluate(coefficients, at):
    """Evaluate coefficients given in descending degree order."""
    value = 0
    for coefficient in coefficients:
        value = _multiply(value, at) ^ coefficient
    return value


def _polynomial_product(left, right):
    product = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            product[i + j] ^= _multiply(a, b)
    return product


def _generator():
    generator = [1]
    for exponent in range(RS_PARITY):
        generator = _polynomial_product(generator, [1, POWERS[exponent]])
    return tuple(generator)


GENERATOR = _generator()


def rs_encode(data):
    """Return a systematic codeword, ending in 32 parity symbols."""
    if len(data) != RS_DATA:
        raise ValueError(f"Reed–Solomon input must be {RS_DATA} bytes")
    remainder = bytearray(data) + bytearray(RS_PARITY)
    for i in range(RS_DATA):
        leading = remainder[i]
        if leading:
            for j, coefficient in enumerate(GENERATOR[1:], 1):
                remainder[i + j] ^= _multiply(leading, coefficient)
    return bytes(data) + bytes(remainder[RS_DATA:])


def _syndromes(word):
    return [_evaluate(word, POWERS[i]) for i in range(RS_PARITY)]


def _locator(sequence):
    """Find a minimal recurrence via Berlekamp–Massey, constant term first."""
    current, previous = [1], [1]
    degree, shift, previous_discrepancy = 0, 1, 1
    for i, value in enumerate(sequence):
        discrepancy = value
        for j in range(1, degree + 1):
            discrepancy ^= _multiply(current[j], sequence[i - j])
        if not discrepancy:
            shift += 1
            continue
        old_current = current.copy()
        current.extend([0] * max(0, shift + len(previous) - len(current)))
        scale = _divide(discrepancy, previous_discrepancy)
        for j, coefficient in enumerate(previous):
            current[shift + j] ^= _multiply(scale, coefficient)
        if 2 * degree <= i:
            degree = i + 1 - degree
            previous, shift, previous_discrepancy = old_current, 1, discrepancy
        else:
            shift += 1
    return current[: degree + 1]


def _magnitudes(positions, syndromes):
    """Solve S[j] = sum(E[i] * X[i]**j) by finite-field elimination."""
    size = len(positions)
    degrees = [RS_TOTAL - 1 - position for position in positions]
    matrix = [
        [POWERS[(row * degree) % 255] for degree in degrees] + [syndromes[row]]
        for row in range(size)
    ]
    for column in range(size):
        pivot = next((i for i in range(column, size) if matrix[i][column]), None)
        if pivot is None:
            raise Uncorrectable("singular Reed–Solomon error system")
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        divisor = matrix[column][column]
        matrix[column] = [_divide(value, divisor) for value in matrix[column]]
        for row in range(size):
            factor = matrix[row][column]
            if row != column and factor:
                matrix[row] = [
                    value ^ _multiply(factor, other)
                    for value, other in zip(matrix[row], matrix[column])
                ]
    return [row[-1] for row in matrix]


def rs_repair(word, erasures=()):
    """Return a repaired codeword and zero-based positions whose bytes changed.

    Retain a placeholder in every erased position. The placeholder's value is
    arbitrary. Independent integrity verification remains necessary.
    """
    if len(word) != RS_TOTAL:
        raise ValueError(f"Reed–Solomon word must be {RS_TOTAL} bytes")
    erasures = tuple(erasures)
    if any(type(i) is not int or not 0 <= i < RS_TOTAL for i in erasures):
        raise ValueError("invalid Reed–Solomon erasure position")
    if len(set(erasures)) != len(erasures):
        raise ValueError("duplicate Reed–Solomon erasure position")
    if len(erasures) > RS_PARITY:
        raise Uncorrectable("too many Reed–Solomon erasures")
    syndromes = _syndromes(word)
    if not any(syndromes):
        return bytes(word), ()

    # For j >= erasure count, multiplying the syndrome series by the
    # known locator cancels each known position's exponential sequence.
    known = [1]
    for position in erasures:
        known = _polynomial_product(known, [1, POWERS[RS_TOTAL - 1 - position]])
    adjusted = [
        reduce(xor, (_multiply(value, syndromes[j - i]) for i, value in enumerate(known)), 0)
        for j in range(len(erasures), RS_PARITY)
    ]
    unknown = _locator(adjusted)
    unknown_errors = len(unknown) - 1
    if 2 * unknown_errors + len(erasures) > RS_PARITY:
        raise Uncorrectable("Reed–Solomon correction radius exceeded")

    locator = _polynomial_product(known, unknown)
    positions = [
        i for i in range(RS_TOTAL)
        if not _evaluate(reversed(locator), POWERS[i + 1])
    ]
    if len(positions) != len(locator) - 1:
        raise Uncorrectable("Reed–Solomon locator has missing or repeated roots")

    repaired = bytearray(word)
    changed = []
    for position, magnitude in zip(positions, _magnitudes(positions, syndromes)):
        if magnitude:
            repaired[position] ^= magnitude
            changed.append(position)
    if any(_syndromes(repaired)):
        raise Uncorrectable("Reed–Solomon candidate retains nonzero syndromes")
    return bytes(repaired), tuple(changed)
