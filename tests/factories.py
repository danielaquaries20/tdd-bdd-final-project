"""
Test Factory to make fake objects for testing
"""
import factory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal
from service.models import Product, Category

class ProductFactory(factory.Factory):
    """Creates fake products for testing"""

    class Meta:
        model = Product

    # Membuat ID berurutan secara otomatis
    id = factory.Sequence(lambda n: n)
    
    # Menghasilkan nama produk dan deskripsi acak
    name = factory.Faker("word")
    description = factory.Faker("text")
    
    # Menghasilkan harga acak antara $0.50 hingga $2000.00
    price = FuzzyDecimal(0.5, 2000.0, 2)
    
    # Ketersediaan acak (True atau False)
    available = FuzzyChoice(choices=[True, False])
    
    # Memilih kategori secara acak dari Enum Category yang ada di model
    category = FuzzyChoice(
        choices=[
            Category.UNKNOWN,
            Category.CLOTHS,
            Category.FOOD,
            Category.HOUSEWARES,
            Category.AUTOMOTIVE,
            Category.TOOLS,
        ]
    )