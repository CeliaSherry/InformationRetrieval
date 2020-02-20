import heapq
import time


# Use min heap to represent a priority queue.  Negate all values.
class MinHeap:
    def __init__(self):
        self.heap = []

    # Insert element into heap and adjust order so heap structure maintained
    def insert(self, value):
        heapq.heappush(self.heap, value)

    # Pops the smallest element
    def pop(self):
        if self.heap == []:
            return None
        return heapq.heappop(self.heap)

    def view_top(self):
        if self.heap == []:
            return None
        else:
            return self.heap[0]

    # Converts iterable into a heap data structure
    def heapify(self):
        heapq.heapify(self.heap)

    def size(self):
        return len(self.heap)


class QueueLink:
    def __init__(self, link, in_links):
        self.link = link
        self.in_links = in_links
        self.timestamp = time.time()

    def add_inlinks(self, count):
        self.in_links += count

    def __lt__(self, other):
        return (self.in_links < other.in_links) or (self.in_links == other.in_links and self.timestamp > other.timestamp)

    def __eq__(self, other):
        return self.in_links == other.in_links

    def __gt__(self, other):
        return (self.in_links > other.in_links) or (
                    self.in_links == other.in_links and self.timestamp < other.timestamp)

    def __cmp__(self, other):
        if self.in_links == other.in_links:
            if self.timestamp < other.timestamp:
                return -1
            return 1
        return self.in_links - other.in_links



















