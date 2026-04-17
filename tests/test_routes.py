######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory
from urllib.parse import quote_plus

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    def test_get_product(self):
        """It should Read a single Product"""
        # 1. Buat satu produk palsu menggunakan fungsi helper yang sudah ada di kelas tes
        test_product = self._create_products(1)[0]

        # 2. Lakukan simulasi HTTP GET request ke endpoint produk menggunakan ID-nya
        response = self.client.get(f"{BASE_URL}/{test_product.id}")

        # 3. Verifikasi bahwa API merespons dengan status 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Ekstrak data JSON dari respons
        data = response.get_json()

        # 5. Pastikan nama produk di JSON sama dengan nama produk yang kita buat
        self.assertEqual(data["name"], test_product.name)

    def test_update_product(self):
        """It should Update an existing Product"""
        # 1. Buat satu produk palsu untuk diuji
        test_product = self._create_products(1)[0]

        # 2. Lakukan perubahan pada salah satu atribut (misalnya deskripsi)
        test_product.description = "This is a new description for testing update"

        # 3. Kirimkan HTTP PUT request ke endpoint produk beserta data terbarunya dalam format JSON
        response = self.client.put(
            f"{BASE_URL}/{test_product.id}", json=test_product.serialize()
        )

        # 4. Verifikasi bahwa API merespons dengan status 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Tarik respons JSON dan pastikan deskripsinya benar-benar sudah berubah
        updated_product = response.get_json()
        self.assertEqual(
            updated_product["description"],
            "This is a new description for testing update",
        )

    def test_delete_product(self):
        """It should Delete a Product"""
        # 1. Buat sekumpulan produk palsu (misalnya 5) untuk memastikan tidak semuanya terhapus
        products = self._create_products(5)

        # 2. Ambil produk pertama sebagai target yang akan dihapus
        product_to_delete = products[0]

        # 3. Kirimkan HTTP DELETE request ke endpoint produk tersebut
        response = self.client.delete(f"{BASE_URL}/{product_to_delete.id}")

        # 4. Verifikasi bahwa API merespons dengan status 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 5. Lakukan double-check dengan mengirim HTTP GET request ke ID yang baru saja dihapus
        response = self.client.get(f"{BASE_URL}/{product_to_delete.id}")

        # 6. Verifikasi bahwa API sekarang merespons dengan status 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_product_list(self):
        """It should Get a list of Products"""
        # 1. Buat sekumpulan produk palsu (misalnya 5 produk) di database
        self._create_products(5)

        # 2. Kirimkan HTTP GET request ke endpoint utama (BASE_URL)
        response = self.client.get(BASE_URL)

        # 3. Verifikasi bahwa API merespons dengan status 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Tarik data JSON dari respons
        data = response.get_json()

        # 5. Pastikan data yang dikembalikan berupa list/array dan panjangnya tepat 5
        self.assertEqual(len(data), 5)

    def test_get_product_list_by_name(self):
        """It should Get a list of Products by Name"""
        # 1. Buat 10 produk palsu di database
        products = self._create_products(10)

        # 2. Ambil nama produk pertama sebagai target pencarian
        test_name = products[0].name

        # 3. Hitung manual berapa banyak produk yang namanya sama dengan target
        name_products = [product for product in products if product.name == test_name]

        # 4. Kirim HTTP GET request dengan query string ?name=nama_produk
        # (Kita gunakan quote_plus agar spasi pada nama diubah menjadi URL-encoded format, misal: %20)
        from urllib.parse import quote_plus

        response = self.client.get(f"{BASE_URL}?name={quote_plus(test_name)}")

        # 5. Verifikasi bahwa API merespons dengan status 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6. Tarik data JSON dan pastikan jumlahnya sama dengan hitungan manual kita
        data = response.get_json()
        self.assertEqual(len(data), len(name_products))

        # 7. Pastikan setiap produk yang dikembalikan benar-benar memiliki nama tersebut
        for product in data:
            self.assertEqual(product["name"], test_name)

    def test_get_product_list_by_category(self):
        """It should Get a list of Products by Category"""
        # 1. Buat 10 produk palsu di database
        products = self._create_products(10)

        # 2. Ambil kategori dari produk pertama sebagai target pencarian
        category = products[0].category

        # 3. Hitung manual berapa banyak produk yang memiliki kategori tersebut
        found_products = [
            product for product in products if product.category == category
        ]
        found_count = len(found_products)

        # 4. Kirim HTTP GET request dengan query string ?category=nama_kategori
        # (Karena category adalah Enum, kita gunakan category.name untuk mendapatkan bentuk teksnya)
        response = self.client.get(f"{BASE_URL}?category={category.name}")

        # 5. Verifikasi bahwa API merespons dengan status 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6. Tarik data JSON dan pastikan jumlahnya sama dengan hitungan manual
        data = response.get_json()
        self.assertEqual(len(data), found_count)

        # 7. Pastikan setiap produk yang dikembalikan benar-benar memiliki kategori yang sesuai
        for product in data:
            self.assertEqual(product["category"], category.name)

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test product",
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["message"], "OK")

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_product = response.get_json()
        # self.assertEqual(new_product["name"], test_product.name)
        # self.assertEqual(new_product["description"], test_product.description)
        # self.assertEqual(Decimal(new_product["price"]), test_product.price)
        # self.assertEqual(new_product["available"], test_product.available)
        # self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
