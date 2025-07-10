-- Standard derivation for AGE
CAST(({{ datediff('year', brthdtc, rfstdtc) }}) AS INT)


