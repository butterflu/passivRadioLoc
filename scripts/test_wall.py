import unittest
import classes

class LineCollision(unittest.TestCase):

    def test_collision(self):
        wall = classes.Wall([1,2],[1,4])
        self.assertTrue(wall.check_line_collision([0,0],[3,3]))
        self.assertFalse(wall.check_line_collision([3,3],[4,4]))
        pass

if __name__ == '__main__':
    unittest.main()